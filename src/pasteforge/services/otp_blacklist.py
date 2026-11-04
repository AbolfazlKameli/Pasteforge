from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.models import OtpBlacklist
from pasteforge.repositories import OtpBlacklistRepository


class OtpBlacklistService:
    def __init__(self, db: AsyncSession):
        self.otp_blacklist_repo = OtpBlacklistRepository(db)

    async def get_active_blacklist_by_email(self, email: str) -> OtpBlacklist | None:
        now = datetime.now(UTC)
        return await self.otp_blacklist_repo.get_active_blacklist_by_email(email, now)

    async def get_blacklist_count_by_email(self, email: str) -> int:
        return await self.otp_blacklist_repo.get_email_blacklist_count(email)

    async def create_blacklist(self, email: str, expires_at: datetime) -> OtpBlacklist:
        return await self.otp_blacklist_repo.create(email=email, expires_at=expires_at)
