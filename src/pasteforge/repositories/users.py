import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.pasteforge.models import User


async def check_email_exists(db: AsyncSession, email: str) -> bool:
    return await db.scalar(sa.select(sa.exists().where(User.email == email)))
