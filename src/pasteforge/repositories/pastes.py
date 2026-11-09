import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from pasteforge.models import Paste, PastesAccessTypes


class PastesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def build_get_by_id_query(
        paste_id: uuid.UUID, access_types: list | None = None, for_update: bool = False, active_only: bool = True
    ) -> sa.Select[Any]:
        stmt = sa.select(Paste).where(Paste.id == paste_id).options(selectinload(Paste.owner))

        if access_types:
            stmt = stmt.where(Paste.access_type.in_(access_types))

        if active_only:
            stmt = stmt.where(Paste.is_active)

        if for_update:
            stmt = stmt.with_for_update()

        return stmt

    async def get_unexpired_by_id(
        self,
        paste_id: uuid.UUID,
        access_types: list[PastesAccessTypes] | None = None,
        for_update: bool = False,
        active_only: bool = True,
    ) -> Paste | None:
        now = datetime.now(UTC)
        result = await self.db.execute(
            self.build_get_by_id_query(paste_id, access_types, for_update, active_only).where(Paste.expires_at > now)
        )
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

    async def save_paste(self, paste: Paste) -> Paste:
        self.db.add(paste)
        await self.db.flush()
        await self.db.refresh(paste)
        return paste
