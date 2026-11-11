import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.models import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def exists_by_email(self, email: str) -> bool:
        stmt = sa.select(sa.exists().where(User.email == email))
        return bool(await self.db.scalar(stmt))

    async def get_by_email(self, email: str, *, for_update: bool = False) -> User | None:
        stmt = sa.select(User).where(User.email == email)

        if for_update:
            stmt = stmt.with_for_update()

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def create(self, email: str, password: str, **values: Any) -> User:
        user = User(email=email, password=password, **values)
        return await self.save_user(user)

    async def update_by_id(self, user_id: uuid.UUID, **values: Any) -> None:
        stmt = sa.update(User).where(User.id == user_id).values(**values)
        await self.db.execute(stmt)

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.flush()

    async def save_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
