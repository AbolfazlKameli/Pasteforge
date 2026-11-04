from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.models import OtpBlacklist


class OtpBlacklistRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_blacklist_by_email(self, email: str, current_time: datetime) -> OtpBlacklist | None:
        stmt = sa.select(OtpBlacklist).where(
            (OtpBlacklist.email == email)
            & ((OtpBlacklist.expires_at >= current_time) | (OtpBlacklist.expires_at.is_(None)))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_email_blacklist_count(self, email: str) -> int:
        result = self.db.scalar(sa.select(sa.func.count()).select_from(OtpBlacklist).where(OtpBlacklist.email == email))
        return await result or 0

    async def create(self, email: str, expires_at: datetime) -> OtpBlacklist:
        blacklist = OtpBlacklist(email=email, expires_at=expires_at)
        self.db.add(blacklist)
        await self.db.flush()
        await self.db.refresh(blacklist)
        return blacklist
