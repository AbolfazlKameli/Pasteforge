import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.exceptions import AuthenticationError, UserAlreadyExistsError
from pasteforge.core.security import hash_value, validate_value
from pasteforge.models import User
from pasteforge.repositories import UserRepository


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.user_repo = UserRepository(db)

    async def get_user_by_email(self, email: str, *, for_update: bool = False) -> User | None:
        return await self.user_repo.get_by_email(email=email, for_update=for_update)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.user_repo.get_by_id(user_id)

    async def exists_by_email(self, email: str) -> bool:
        return await self.user_repo.exists_by_email(email)

    async def create_user(self, email: str, password: str, **values: Any) -> User:
        if await self.exists_by_email(email):
            raise UserAlreadyExistsError()

        return await self.user_repo.create(email=email, password=hash_value(password), **values)

    async def update_user_data(self, user_id: uuid.UUID, **values: Any) -> bool:
        email = values.pop("email", None)
        email_changed = False

        if email is not None:
            if await self.exists_by_email(email):
                raise UserAlreadyExistsError()

            email_changed = True

        await self.user_repo.update_by_id(user_id, **values)
        return email_changed

    async def update_user_email(self, user_id: uuid.UUID, email: str) -> None:
        await self.user_repo.update_by_id(user_id, email=email)

    async def delete_user(self, user: User) -> None:
        await self.user_repo.delete(user)

    @staticmethod
    def validate_user_password(user: User, password: str) -> bool:
        return validate_value(user.password, password)

    async def change_password(self, user: User, new_password: str, old_password: str | None = None) -> None:
        if old_password is not None:
            if not self.validate_user_password(user, old_password):
                raise AuthenticationError("Current password is incorrect.")

        user.password = hash_value(new_password)
        await self.user_repo.save_user(user)

    async def authenticate_user_by_email(self, email: str, password: str) -> User:
        user = await self.get_user_by_email(email)

        if user is None or not user.is_active or not self.validate_user_password(user, password):
            raise AuthenticationError(
                "Email or password incorrect. If you believe your account is deactivated, contact support."
            )

        return user

    async def get_active_user_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.get_user_by_id(user_id)

        if user is None or not user.is_active:
            raise AuthenticationError(
                "Email or password incorrect. If you believe your account is deactivated, contact support."
            )

        return user
