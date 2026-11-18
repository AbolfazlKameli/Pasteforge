from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from pasteforge.core.config import configs

celery_engine = create_async_engine(url=configs.DATABASE_URL, poolclass=NullPool)

CelerySessionLocal = async_sessionmaker(bind=celery_engine, expire_on_commit=False)
