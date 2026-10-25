import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.models import Otp, OtpBlacklist, TokenObtainPair, TokenPairStatuses


async def get_active_blacklist_by_email(db: AsyncSession, email: str, current_time: datetime) -> OtpBlacklist | None:
    stmt = sa.select(OtpBlacklist).where(
        (OtpBlacklist.email == email)
        & ((OtpBlacklist.expires_at >= current_time) | (OtpBlacklist.expires_at.is_(None)))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_blacklist_count(db: AsyncSession, email: str) -> int:
    return await db.scalar(sa.select(sa.func.count()).select_from(OtpBlacklist).where(OtpBlacklist.email == email)) or 0


async def get_otp(db: AsyncSession, email: str, for_update: bool = False) -> Otp | None:
    stmt = sa.select(Otp).where(Otp.email == email)

    if for_update:
        stmt = stmt.with_for_update()

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_otp(db: AsyncSession, email: str, code: str, expires_at: datetime):
    otp = Otp(email=email, expires_at=expires_at)
    otp.set_code(code)
    db.add(otp)
    await db.flush()


async def reset_otp_attempts(db: AsyncSession, otp: Otp):
    return await db.execute(sa.update(Otp).where(Otp.id == otp.id).values(attempts=0))


async def get_blacklist_by_sid(db: AsyncSession, sid: uuid.UUID) -> TokenObtainPair:
    result = await db.execute(
        sa.select(TokenObtainPair).where(
            (TokenObtainPair.status == TokenPairStatuses.blacklisted) & (TokenObtainPair.sid == sid)
        )
    )
    return result.scalar_one_or_none()


async def token_pair_exists(db: AsyncSession, sid: uuid.UUID) -> bool:
    return await db.scalar(sa.select(sa.exists().where(TokenObtainPair.sid == sid)))


async def blacklist_token_pair_by_sid(db: AsyncSession, sid: uuid.UUID) -> None:
    await db.execute(
        sa.update(TokenObtainPair).where(TokenObtainPair.sid == sid).values(status=TokenPairStatuses.blacklisted)
    )
    await db.flush()


async def blacklist_token_pair_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        sa.update(TokenObtainPair)
        .where(TokenObtainPair.owner_id == user_id)
        .values(status=TokenPairStatuses.blacklisted)
    )
    await db.flush()
