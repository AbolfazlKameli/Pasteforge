import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import sqlalchemy as sa
from fastapi import Depends

from pasteforge.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from pasteforge.core.security import hash_value, validate_value
from pasteforge.models import Paste, PastesAccessTypes
from pasteforge.repositories import PastesRepository
from pasteforge.schemas.pastes import PasteFilter, PasteOut


class PasteService:
    def __init__(self, paste_repo: Annotated[PastesRepository, Depends(PastesRepository)]) -> None:
        self.paste_repo = paste_repo

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

    def build_get_pastes_by_owner_query(self, user_id: uuid.UUID) -> sa.Select[Paste]:
        return self.paste_repo.build_get_by_owner_query(user_id)

    @staticmethod
    def filter_query(stmt: sa.Select[Paste], filters: PasteFilter) -> sa.Select[Paste]:
        if filters.access_type is not None:
            stmt = stmt.where(Paste.access_type == filters.access_type)

        if filters.syntax is not None:
            stmt = stmt.where(Paste.syntax == filters.syntax)

        if filters.created_after is not None:
            stmt = stmt.where(Paste.created_at >= filters.created_after)

        if filters.created_before is not None:
            stmt = stmt.where(Paste.created_at <= filters.created_before)

        if filters.expired:
            stmt = stmt.where(Paste.expires_at < datetime.now(UTC))

        if filters.search is not None:
            stmt = stmt.where(Paste.content.ilike(f"%{filters.search}%"))

        return stmt

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
        if (paste := await self.paste_repo.get_paste_from_cache(paste_id)) is not None:
            return paste

        paste = await self.get_unexpired_paste_by_id(paste_id, [PastesAccessTypes.public, PastesAccessTypes.private])

        if paste.access_type == PastesAccessTypes.private:
            if user_id is None:
                raise AuthenticationError("Unauthenticated users can only retrieve public pastes.")

            self.check_ownership(paste, user_id)

        await self.paste_repo.set_paste_cache(paste)

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

        return updated_paste

    async def update_manageable_paste_expiration(
        self, paste_id: uuid.UUID, user_id: uuid.UUID, password: str | None, expires_at: datetime
    ) -> Paste:
        paste = await self.get_manageable_paste_by_id(paste_id, list(PastesAccessTypes), for_update=True)

        self.check_ownership(paste, user_id)
        self.validate_paste_password(paste, password)

        updated_paste = await self.paste_repo.update(paste, expires_at=expires_at)

        return updated_paste

    async def delete_paste_by_id(self, paste_id: uuid.UUID, user_id: uuid.UUID, password: str | None) -> None:
        paste = await self.get_unexpired_paste_by_id(paste_id, list(PastesAccessTypes), for_update=True)

        self.check_ownership(paste, user_id)

        self.validate_paste_password(paste, password)

        await self.paste_repo.delete(paste)
