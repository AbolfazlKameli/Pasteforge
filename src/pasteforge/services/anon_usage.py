from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.core.exceptions import ForbiddenError
from pasteforge.core.security import hash_ip
from pasteforge.repositories import AnonymousUsageRepository


class AnonymousUsageService:
    def __init__(self, db: AsyncSession) -> None:
        self.usage_repo = AnonymousUsageRepository(db)

    async def validate_paste_usage(self, ip: str) -> None:
        usage = await self.usage_repo.increment_paste_usage(hashed_ip=hash_ip(ip))

        if usage > configs.ANON_USER_USAGE_LIMIT:
            raise ForbiddenError("You've reached the anonymous paste creation limit. Log in to create more pastes.")
