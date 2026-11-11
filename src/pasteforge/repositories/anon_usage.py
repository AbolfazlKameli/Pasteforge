from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.models import AnonymousUsage


class AnonymousUsageRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def increment_paste_usage(self, hashed_ip: str) -> int:
        stmt = (
            insert(AnonymousUsage)
            .values(hashed_ip=hashed_ip, counter=1)
            .on_conflict_do_update(
                index_elements=[AnonymousUsage.hashed_ip],
                set_={"counter": AnonymousUsage.counter + 1},
                where=AnonymousUsage.counter < configs.ANON_USER_USAGE_LIMIT,
            )
            .returning(AnonymousUsage.counter)
        )

        result = await self.db.execute(stmt)
        usage = result.scalar_one_or_none()

        return usage if usage is not None else configs.ANON_USER_USAGE_LIMIT + 1
