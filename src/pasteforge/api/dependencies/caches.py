from typing import Annotated

from fastapi import Depends
from redis_fastapi import AsyncRedisDep, CacheBackend

from pasteforge.core.config import configs


async def get_pastes_cache(redis: AsyncRedisDep) -> CacheBackend:
    return CacheBackend(redis, eviction_group=configs.CACHE_GROUP_PASTES)


PasteCacheDep = Annotated[CacheBackend, Depends(get_pastes_cache)]
