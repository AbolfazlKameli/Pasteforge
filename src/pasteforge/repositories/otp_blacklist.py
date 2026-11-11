from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.models import OtpBlacklist


class OtpBlacklistRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_active_by_email(self, email: str, current_time: datetime) -> OtpBlacklist | None:
        stmt = sa.select(OtpBlacklist).where(
            (OtpBlacklist.email == email)
            & ((OtpBlacklist.expires_at >= current_time) | (OtpBlacklist.expires_at.is_(None)))
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_email(self, email: str) -> int:
        stmt = sa.select(sa.func.count()).select_from(OtpBlacklist).where(OtpBlacklist.email == email)

        result = await self.db.scalar(stmt)
        return result or 0

    async def create(self, email: str, expires_at: datetime | None) -> OtpBlacklist:
        blacklist = OtpBlacklist(email=email, expires_at=expires_at)
        self.db.add(blacklist)
        await self.db.flush()

        return blacklist
