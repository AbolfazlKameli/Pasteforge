import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_email_exists(self, email: str) -> bool:
        return await self.db.scalar(sa.select(sa.exists().where(User.email == email)))

    async def get_by_email(self, email: str, for_update: bool = False) -> User | None:
        stmt = sa.select(User).where(User.email == email)

        if for_update:
            stmt = stmt.with_for_update()

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        user = await self.db.get(User, user_id)
        return user

    async def create(self, email: str, password: str, **kwargs) -> User:
        user = User(email=email, password=password, **kwargs)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_by_id(self, user_id: uuid.UUID, **kwargs) -> None:
        await self.db.execute(sa.update(User).where(User.id == user_id).values(**kwargs))
        await self.db.flush()

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.flush()

    async def save_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
