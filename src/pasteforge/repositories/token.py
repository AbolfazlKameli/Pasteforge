import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.models import TokenObtainPair, TokenPairStatuses


class TokenPairRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_sid(self, sid: uuid.UUID) -> TokenObtainPair | None:
        stmt = sa.select(TokenObtainPair).where(TokenObtainPair.sid == sid)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_blacklisted_by_sid(self, sid: uuid.UUID) -> TokenObtainPair | None:
        stmt = sa.select(TokenObtainPair).where(
            (TokenObtainPair.sid == sid) & (TokenObtainPair.status == TokenPairStatuses.blacklisted)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def blacklist_by_sid(self, sid: uuid.UUID) -> None:
        stmt = (
            sa.update(TokenObtainPair)
            .where((TokenObtainPair.sid == sid) & (TokenObtainPair.status != TokenPairStatuses.blacklisted))
            .values(status=TokenPairStatuses.blacklisted)
        )
        await self.db.execute(stmt)

    async def blacklist_by_user_id(self, user_id: uuid.UUID) -> None:
        stmt = (
            sa.update(TokenObtainPair)
            .where((TokenObtainPair.owner_id == user_id) & (TokenObtainPair.status != TokenPairStatuses.blacklisted))
            .values(status=TokenPairStatuses.blacklisted)
        )
        await self.db.execute(stmt)

    async def create(self, sid: uuid.UUID, owner_id: uuid.UUID) -> TokenObtainPair:
        token_pair = TokenObtainPair(sid=sid, owner_id=owner_id)
        self.db.add(token_pair)
        await self.db.flush()
        return token_pair

    async def exists_by_sid(self, sid: uuid.UUID) -> bool:
        stmt = sa.select(sa.exists().where(TokenObtainPair.sid == sid))
        return bool(await self.db.scalar(stmt))
