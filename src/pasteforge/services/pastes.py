import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.core.exceptions import AuthenticationError, ValidationError
from pasteforge.core.security import hash_value
from pasteforge.models import Paste, PastesAccessTypes
from pasteforge.repositories import PastesRepository


class PasteService:
    def __init__(self, db: AsyncSession):
        self.paste_repo = PastesRepository(db)

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
