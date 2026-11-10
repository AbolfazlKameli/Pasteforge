import uuid
from datetime import UTC, datetime, timedelta

from redis_fastapi import CacheBackend
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.core.exceptions import AuthenticationError, ForbiddenError, NotFoundError, ValidationError
from pasteforge.core.security import hash_value, validate_value
from pasteforge.models import Paste, PastesAccessTypes
from pasteforge.repositories import PastesRepository
from pasteforge.schemas.pastes import PasteOut


class PasteService:
    def __init__(self, db: AsyncSession, cache: CacheBackend):
        self.paste_repo = PastesRepository(db)
        self.cache = cache

    @staticmethod
    def check_ownership(paste: Paste, user_id: uuid.UUID) -> None:
        if paste.owner_id != user_id:
            raise NotFoundError()

    @staticmethod
    def validate_paste_password(paste: Paste, password: str) -> None:
        # noinspection PyTypeChecker
        if not validate_value(paste.password, password):
            raise ForbiddenError("Incorrect password.")

    async def get_unexpired_paste_by_id(
        self, paste_id: uuid.UUID, access_type: list[PastesAccessTypes], for_update: bool = False
    ) -> Paste | None:
        paste = await self.paste_repo.get_unexpired_by_id(paste_id, access_type, for_update)
        if paste is None:
            raise NotFoundError()
        return paste

    async def get_manageable_paste_by_id(
            self, paste_id: uuid.UUID, access_type: list[PastesAccessTypes], for_update: bool = False
    ):
        paste = await self.paste_repo.get_manageable_by_id(paste_id, access_type, for_update)
        if paste is None:
            raise NotFoundError()
        return paste

    async def get_authorized_paste_by_id(self, paste_id: uuid.UUID, user_id: uuid.UUID | None) -> PasteOut | None:
        paste = await self.cache.get(f"paste:{paste_id}")
        if paste is not None:
            now = datetime.now(UTC)
            paste = PasteOut.model_validate_json(paste)

            if paste.expires_at < now:
                await self.cache.delete(f"paste:{paste_id}")
                raise NotFoundError()

            return paste

        paste = await self.get_unexpired_paste_by_id(paste_id, [PastesAccessTypes.public, PastesAccessTypes.private])

        if paste.access_type == PastesAccessTypes.private:
            if user_id is None:
                raise AuthenticationError("Unauthenticated users can only retrieve public pastes.")

            self.check_ownership(paste, user_id)

        if paste.access_type == PastesAccessTypes.public:
            serialized = PasteOut.model_validate(paste).model_dump_json()
            await self.cache.set(f"paste:{paste.id}", serialized, ttl=configs.PUBLIC_PASTE_CACHE_MAX_AGE)

        return PasteOut.model_validate(paste)

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
        expires_at: datetime,
        password: str | None,
        owner_id: uuid.UUID | None,
    ) -> Paste:
        if size_bytes <= 0:
            raise ValueError("Paste content must not be empty.")

        if size_bytes > configs.MAX_CONTENT_SIZE:
            raise ValueError(f"Paste content must not exceed {configs.MAX_CONTENT_SIZE} bytes.")

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
        self, paste_id: uuid.UUID, user_id: uuid.UUID, password: str | None, new_password: str | None, **update_data
    ) -> Paste:
        paste = await self.get_unexpired_paste_by_id(paste_id, [ac for ac in PastesAccessTypes], for_update=True)

        self.check_ownership(paste, user_id)

        if paste.access_type == PastesAccessTypes.password_protected:
            if password is None:
                raise ValidationError("A password is required for password-protected pastes.")

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

        return await self.paste_repo.update(paste, **update_data)

    async def update_manageable_paste_expiration(
            self, paste_id: uuid.UUID, user_id: uuid.UUID, password: str | None, expires_at: datetime
    ) -> Paste:
        paste = await self.get_manageable_paste_by_id(paste_id, [ac for ac in PastesAccessTypes], for_update=True)

        self.check_ownership(paste, user_id)

        if paste.access_type == PastesAccessTypes.password_protected:
            if password is None:
                raise ValidationError("A password is required for password-protected pastes.")

            self.validate_paste_password(paste, password)

        return await self.paste_repo.update(paste, expires_at=expires_at)
