from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.models import OtpBlacklist
from pasteforge.repositories import OtpBlacklistRepository


class OtpBlacklistService:
    def __init__(self, db: AsyncSession) -> None:
        self.otp_blacklist_repo = OtpBlacklistRepository(db)

    async def get_active_by_email(self, email: str) -> OtpBlacklist | None:
        return await self.otp_blacklist_repo.get_active_by_email(email=email, current_time=datetime.now(UTC))

    async def count_by_email(self, email: str) -> int:
        return await self.otp_blacklist_repo.count_by_email(email=email)

    async def create(self, email: str, expires_at: datetime | None) -> OtpBlacklist:
        return await self.otp_blacklist_repo.create(email=email, expires_at=expires_at)
