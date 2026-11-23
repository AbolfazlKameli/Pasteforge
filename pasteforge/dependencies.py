from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from redis import asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.db.database import SessionLocal
from pasteforge.infrastructure.redis_pool import redis_conn


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        # noinspection PyBroadException
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_redis() -> redis.Redis:
    return redis_conn


db_dependency = Annotated[AsyncSession, Depends(get_db)]
redis_dependency = Annotated[redis.Redis, Depends(get_redis)]
