import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.models import Paste, PastesAccessTypes


class PastesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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
