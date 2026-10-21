from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from src.pasteforge.models import Otp, OtpBlacklist, RefreshTokenBlacklist


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


async def get_blacklist_by_refresh_token(db: AsyncSession, refresh_token: str) -> RefreshTokenBlacklist:
    result = await db.execute(sa.select(RefreshTokenBlacklist).where(RefreshTokenBlacklist.refresh == refresh_token))
    return result.scalar_one_or_none()


async def create_token_blacklist(db: AsyncSession, refresh_token: str) -> None:
    blacklist = RefreshTokenBlacklist(refresh=refresh_token)
    db.add(blacklist)
    await db.commit()
