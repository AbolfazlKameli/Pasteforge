import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from pasteforge.models import Paste, PastesAccessTypes


class PastesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
            self, paste_id: uuid.UUID, access_types: list | None = None, for_update: bool = False
    ) -> Paste | None:
        stmt = sa.select(Paste).where(Paste.id == paste_id).options(joinedload(Paste.owner))

        if access_types:
            stmt = stmt.where(Paste.access_type.in_(access_types))

        if for_update:
            stmt = stmt.with_for_update()

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
        self.db.add(paste)
        await self.db.flush()
        await self.db.refresh(paste)
        return paste
