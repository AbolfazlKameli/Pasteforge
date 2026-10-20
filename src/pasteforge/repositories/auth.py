from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.pasteforge.models import OtpBlacklist


async def get_active_blacklist_by_email(db: AsyncSession, email: str, current_time: datetime) -> OtpBlacklist | None:
    stmt = (
        sa.select(OtpBlacklist)
        .where(
            (OtpBlacklist.email == email) &
            (
                    (OtpBlacklist.expires_at >= current_time) | (OtpBlacklist.expires_at.is_(None))
            )
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_blacklist_count(db: AsyncSession, email: str) -> int:
    return await db.scalar(sa.select(sa.func.count()).select_from(OtpBlacklist).where(OtpBlacklist.email == email))
