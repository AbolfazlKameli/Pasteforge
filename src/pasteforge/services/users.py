import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.exceptions import AuthenticationError, UserAlreadyExistsError
from pasteforge.core.security import hash_value, validate_value
from pasteforge.models import User
from pasteforge.repositories.users import UserRepository


class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.user_repo.get_by_email(email, False)

    async def get_user_by_email_for_update(self, email: str) -> User | None:
        return await self.user_repo.get_by_email(email, True)

    async def user_exists_with_email(self, email: str) -> bool:
        return await self.user_repo.is_email_exists(email)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.user_repo.get_by_id(user_id)

    async def create_user(self, email: str, password: str, **kwargs) -> User:
        if await self.user_repo.is_email_exists(email):
            raise UserAlreadyExistsError()

        hashed_password = hash_value(password)

        return await self.user_repo.create(email, hashed_password, **kwargs)

    async def update_user_data(self, user_id: uuid.UUID, **kwargs) -> bool:
        email = kwargs.pop("email", None)
        email_changed = False

        if email is not None:
            if await self.user_repo.is_email_exists(email):
                raise UserAlreadyExistsError()

            email_changed = True

        await self.user_repo.update_by_id(user_id, **kwargs)

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
            self.validate_user_password(user, old_password)

        user.password = hash_value(new_password)

        await self.user_repo.save_user(user)

    async def authenticate_user_by_email(self, email: str, password: str) -> User | None:
        user = await self.get_user_by_email(email)

        if (user is None) or (not user.is_active) or (not self.validate_user_password(user, password)):
            raise AuthenticationError(
                "Email or password incorrect. if you believe your account is deactivated, call support."
            )

        return user

    async def get_active_user_by_id(self, user_id: uuid.UUID) -> User | None:
        user = await self.get_user_by_id(user_id)

        if user is None or not user.is_active:
            raise AuthenticationError(
                "Email or password incorrect. if you believe your account is deactivated, call support."
            )

        return user
