from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.pasteforge.models.authentication import OtpBlacklist


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
