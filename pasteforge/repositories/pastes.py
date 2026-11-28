import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

import sqlalchemy as sa
from fastapi import Depends
from redis_fastapi import AsyncRedisDep, CacheBackend
from sqlalchemy.orm import joinedload

from pasteforge.core.config import configs
from pasteforge.dependencies import db_dependency
from pasteforge.models import Paste, PastesAccessTypes
from pasteforge.schemas.pastes import PasteOut


async def get_pastes_cache(redis: AsyncRedisDep) -> CacheBackend:
    return CacheBackend(redis, eviction_group=configs.CACHE_GROUP_PASTES)


PasteCacheDep = Annotated[CacheBackend, Depends(get_pastes_cache)]


class PastesRepository:
    CACHE_KEY_PREFIX = "paste:"

    def __init__(self, db: db_dependency, cache: PasteCacheDep) -> None:
        self.db = db
        self.cache = cache

    @classmethod
    def get_cache_key(cls, paste_id: uuid.UUID) -> str:
        return f"{cls.CACHE_KEY_PREFIX}{paste_id}"

    @staticmethod
    def build_get_by_id_query(
        paste_id: uuid.UUID, access_types: list[PastesAccessTypes] | None = None, *, for_update: bool = False
    ) -> sa.Select[Paste]:
        stmt = sa.select(Paste).where(Paste.id == paste_id).options(joinedload(Paste.owner))

        if access_types is not None:
            stmt = stmt.where(Paste.access_type.in_(access_types))

        if for_update:
            stmt = stmt.with_for_update(of=Paste)

        return stmt

    @staticmethod
    def build_get_by_owner_query(owner_id: uuid.UUID) -> sa.Select[Paste]:
        return sa.select(Paste).where(Paste.owner_id == owner_id)

    async def set_paste_cache(self, paste: Paste) -> None:
        paste_out = PasteOut.model_validate(paste)
        if paste.access_type == PastesAccessTypes.public:
            await self.cache.set(
                self.get_cache_key(paste.id),
                paste_out.model_dump_json(),
                ttl=configs.PUBLIC_PASTE_CACHE_MAX_AGE,
            )

    async def get_paste_from_cache(self, paste_id: uuid.UUID) -> PasteOut | None:
        cache_key = self.get_cache_key(paste_id)
        cached_paste = await self.cache.get(cache_key)

        if cached_paste is not None:
            paste_out = PasteOut.model_validate_json(cached_paste)

            if paste_out.access_type == PastesAccessTypes.public and paste_out.expires_at > datetime.now(UTC):
                return paste_out

            await self.cache.delete(cache_key)

        return None

    async def invalidate_paste_cache(self, paste_id: uuid.UUID) -> None:
        await self.cache.delete(self.get_cache_key(paste_id))

    async def get_unexpired_by_id(
        self, paste_id: uuid.UUID, access_types: list[PastesAccessTypes] | None = None, *, for_update: bool = False
    ) -> Paste | None:
        now = datetime.now(UTC)

        stmt = self.build_get_by_id_query(paste_id=paste_id, access_types=access_types, for_update=for_update).where(
            Paste.expires_at > now
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_manageable_by_id(
        self, paste_id: uuid.UUID, access_types: list[PastesAccessTypes] | None = None, *, for_update: bool = False
    ) -> Paste | None:
        now = datetime.now(UTC)

        stmt = self.build_get_by_id_query(paste_id=paste_id, access_types=access_types, for_update=for_update).where(
            (Paste.expires_at <= now) & (Paste.expires_at + configs.PASTE_MANAGEMENT_TIME_WINDOW > now)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        content: str,
        syntax: str,
        size_bytes: int,
        access_type: PastesAccessTypes,
        expires_at: datetime,
        password: str | None,
        owner_id: uuid.UUID | None,
    ) -> Paste:
        paste = Paste(
            content=content,
            syntax=syntax,
            size_bytes=size_bytes,
            access_type=access_type,
            expires_at=expires_at,
            password=password,
            owner_id=owner_id,
        )

        return await self.save_paste(paste)

    async def update(self, paste: Paste, **update_data: Any) -> Paste:
        for key, value in update_data.items():
            setattr(paste, key, value)

        await self.invalidate_paste_cache(paste.id)

        return await self.save_paste(paste)

    async def delete(self, paste: Paste) -> None:
        await self.db.delete(paste)
        await self.db.flush()
        await self.invalidate_paste_cache(paste.id)

    async def delete_expired_anonymous(self) -> int:
        now = datetime.now(UTC)
        result = await self.db.execute(sa.delete(Paste).where((Paste.expires_at < now) & (Paste.owner_id.is_(None))))
        return result.rowcount

    async def delete_unmanageable(self) -> int:
        now = datetime.now(UTC)
        stmt = sa.delete(Paste).where(
            (Paste.expires_at + configs.PASTE_MANAGEMENT_TIME_WINDOW < now) & (Paste.owner_id.is_not(None))
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def save_paste(self, paste: Paste) -> Paste:
        self.db.add(paste)
        await self.db.flush()
        await self.db.refresh(paste)
        return paste
