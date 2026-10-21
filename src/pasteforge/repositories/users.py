import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.pasteforge.models import User


async def check_email_exists(db: AsyncSession, email: str) -> bool:
    return await db.scalar(sa.select(sa.exists().where(User.email == email)))


async def get_user_by_email(db: AsyncSession, email: str, for_update: bool = False) -> User | None:
    stmt = sa.select(User).where(User.email == email)

    if for_update:
        stmt = stmt.with_for_update()

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID):
    user = await db.get(User, user_id)
    return user
