import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.models import TokenObtainPair, TokenPairStatuses


class TokenPairRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_blacklisted_by_sid(self, sid: uuid.UUID) -> TokenObtainPair | None:
        result = await self.db.execute(
            sa.select(TokenObtainPair).where(
                (TokenObtainPair.status == TokenPairStatuses.blacklisted) & (TokenObtainPair.sid == sid)
            )
        )
        return result.scalar_one_or_none()

    async def blacklist_token_pair_by_sid(self, sid: uuid.UUID) -> None:
        await self.db.execute(
            sa.update(TokenObtainPair).where(TokenObtainPair.sid == sid).values(status=TokenPairStatuses.blacklisted)
        )
        await self.db.flush()

    async def blacklist_token_pair_by_user_id(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            sa.update(TokenObtainPair)
            .where(TokenObtainPair.owner_id == user_id)
            .values(status=TokenPairStatuses.blacklisted)
        )
        await self.db.flush()

    async def create(self, sid: uuid.UUID, owner_id: uuid.UUID) -> TokenObtainPair:
        token_pair = TokenObtainPair(sid=sid, owner_id=owner_id)
        self.db.add(token_pair)
        await self.db.flush()
        await self.db.refresh(token_pair)
        return token_pair

    async def is_pair_exists(self, sid: uuid.UUID) -> bool:
        return await self.db.scalar(sa.select(sa.exists().where(TokenObtainPair.sid == sid)))
