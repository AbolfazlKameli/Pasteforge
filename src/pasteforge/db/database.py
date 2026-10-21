from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.pasteforge.core.config import configs

engine = create_async_engine(
    url=configs.DATABASE_URL,
    pool_size=configs.DATABASE_POOL_SIZE,
    max_overflow=configs.DATABASE_MAX_OVERFLOW,
)

SessionLocal = async_sessionmaker(bind=engine)


class Base(DeclarativeBase):
    type_annotation_map = {datetime: DateTime(timezone=True)}
