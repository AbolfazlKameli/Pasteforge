import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from redis_fastapi import CacheBackend
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from pasteforge.core.security import hash_value, validate_value
from pasteforge.models import Paste, PastesAccessTypes
from pasteforge.repositories import PastesRepository
from pasteforge.schemas.pastes import PasteOut


class PasteService:
    CACHE_KEY_PREFIX = "paste:"

    def __init__(self, db: AsyncSession, cache: CacheBackend):
        self.paste_repo = PastesRepository(db)
        self.cache = cache

    @classmethod
    def get_cache_key(cls, paste_id: uuid.UUID) -> str:
        return f"{cls.CACHE_KEY_PREFIX}{paste_id}"

    @staticmethod
    def check_ownership(paste: Paste, user_id: uuid.UUID) -> None:
        if paste.owner_id != user_id:
            raise NotFoundError()

    @staticmethod
    def validate_paste_password(paste: Paste, password: str) -> None:
        if paste.access_type == PastesAccessTypes.password_protected:
            if password is None:
                raise ValidationError("A password is required for password-protected pastes.")

            if not validate_value(paste.password, password):
                raise ValidationError("Incorrect password.")

    async def invalidate_paste_cache(self, paste_id: uuid.UUID) -> None:
        await self.cache.delete(self.get_cache_key(paste_id))

    async def get_unexpired_paste_by_id(
        self, paste_id: uuid.UUID, access_types: list[PastesAccessTypes], *, for_update: bool = False
    ) -> Paste:
        paste = await self.paste_repo.get_unexpired_by_id(
            paste_id=paste_id, access_types=access_types, for_update=for_update
        )

        if paste is None:
            raise NotFoundError()

        return paste

    async def get_manageable_paste_by_id(
        self, paste_id: uuid.UUID, access_types: list[PastesAccessTypes], *, for_update: bool = False
    ) -> Paste:
        paste = await self.paste_repo.get_manageable_by_id(
            paste_id=paste_id, access_types=access_types, for_update=for_update
        )

        if paste is None:
            raise NotFoundError()

        return paste

    async def get_authorized_paste_by_id(self, paste_id: uuid.UUID, user_id: uuid.UUID | None) -> PasteOut | None:
        cache_key = self.get_cache_key(paste_id)
        cached_paste = await self.cache.get(cache_key)

        if cached_paste is not None:
            paste_out = PasteOut.model_validate_json(cached_paste)

            if paste_out.access_type == PastesAccessTypes.public.value and paste_out.expires_at > datetime.now(UTC):
                return paste_out

            await self.cache.delete(cache_key)

        paste = await self.get_unexpired_paste_by_id(paste_id, [PastesAccessTypes.public, PastesAccessTypes.private])

        if paste.access_type == PastesAccessTypes.private:
            if user_id is None:
                raise AuthenticationError("Unauthenticated users can only retrieve public pastes.")

            self.check_ownership(paste, user_id)

        paste_out = PasteOut.model_validate(paste)

        if paste.access_type == PastesAccessTypes.public:
            await self.cache.set(cache_key, paste_out.model_dump_json(), ttl=configs.PUBLIC_PASTE_CACHE_MAX_AGE)

        return paste_out

    async def get_protected_paste_by_id(self, paste_id: uuid.UUID, password: str):
        paste = await self.get_unexpired_paste_by_id(paste_id, [PastesAccessTypes.password_protected])
        self.validate_paste_password(paste, password)
        return paste

    async def create_paste(
        self,
        content: str,
        syntax: str,
        size_bytes: int,
        access_type: PastesAccessTypes,
        expires_at: datetime | None,
        password: str | None,
        owner_id: uuid.UUID | None,
    ) -> Paste:
        hashed_password = None

        if owner_id is None:
            if access_type != PastesAccessTypes.public:
                raise AuthenticationError("Unauthenticated users can only create public pastes.")

            if expires_at is not None:
                raise AuthenticationError("Expiration is automatically set to 10 minutes for anonymous pastes.")

            if password is not None:
                raise AuthenticationError("Anonymous users cannot create password-protected pastes.")

            expires_at = datetime.now(UTC) + timedelta(minutes=10)

        else:
            if expires_at is None:
                raise ValidationError("Expiration is required for authenticated pastes.")

            if access_type == PastesAccessTypes.password_protected:
                if password is None:
                    raise ValidationError("A password is required for password-protected pastes.")

                hashed_password = hash_value(password)

            elif password is not None:
                raise ValidationError("A password can only be set for password-protected pastes.")
        return await self.paste_repo.create(
            content, syntax, size_bytes, access_type, expires_at, hashed_password, owner_id
        )

    async def update_paste(
        self,
        paste_id: uuid.UUID,
        user_id: uuid.UUID,
        password: str | None,
        new_password: str | None,
        **update_data: Any,
    ) -> Paste:
        paste = await self.get_unexpired_paste_by_id(paste_id, list(PastesAccessTypes), for_update=True)

        self.check_ownership(paste, user_id)
        self.validate_paste_password(paste, password)

        access_type = update_data.get("access_type")

        if access_type == PastesAccessTypes.password_protected:
            if paste.access_type != PastesAccessTypes.password_protected:
                if new_password is None:
                    raise ValidationError("A new password is required to protect a paste.")

            if new_password is not None:
                update_data["password"] = hash_value(new_password)

        elif access_type is not None:
            update_data["password"] = None

        updated_paste = await self.paste_repo.update(paste, **update_data)

        await self.invalidate_paste_cache(paste_id)

        return updated_paste

    async def update_manageable_paste_expiration(
        self, paste_id: uuid.UUID, user_id: uuid.UUID, password: str | None, expires_at: datetime
    ) -> Paste:
        paste = await self.get_manageable_paste_by_id(paste_id, list(PastesAccessTypes), for_update=True)

        self.check_ownership(paste, user_id)
        self.validate_paste_password(paste, password)

        updated_paste = await self.paste_repo.update(paste, expires_at=expires_at)

        await self.invalidate_paste_cache(paste_id)

        return updated_paste

    async def delete_paste_by_id(self, paste_id: uuid.UUID, user_id: uuid.UUID, password: str | None) -> None:
        paste = await self.get_unexpired_paste_by_id(paste_id, list(PastesAccessTypes), for_update=True)

        self.check_ownership(paste, user_id)

        if password is not None:
            self.validate_paste_password(paste, password)

        await self.paste_repo.delete(paste)
        await self.invalidate_paste_cache(paste_id)
