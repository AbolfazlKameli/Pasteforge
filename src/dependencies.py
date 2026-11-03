from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.db.database import SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        # noinspection PyBroadException
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


db_dependency = Annotated[AsyncSession, Depends(get_db)]
