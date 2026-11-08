from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.models import AnonymousUsage


class AnonymousUsageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_paste_usage(self, hashed_ip: str) -> int:
        stmt = (
            insert(AnonymousUsage)
            .values(hashed_ip=hashed_ip, counter=1)
            .on_conflict_do_update(
                index_elements=[AnonymousUsage.hashed_ip],
                set_={"counter": AnonymousUsage.counter + 1},
                where=(AnonymousUsage.counter < configs.ANON_USER_USAGE_LIMIT),
            )
            .returning(AnonymousUsage.counter)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() or configs.ANON_USER_USAGE_LIMIT + 10
