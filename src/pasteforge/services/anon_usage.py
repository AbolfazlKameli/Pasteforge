from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.security import hash_ip
from pasteforge.repositories import AnonymousUsageRepository


class AnonymousUsageService:
    def __init__(self, db: AsyncSession):
        self.usage_repo = AnonymousUsageRepository(db)

    async def get_remaining_usage(self, ip: str) -> int:
        return await self.usage_repo.get_remaining_usage(hashed_ip=hash_ip(ip))
