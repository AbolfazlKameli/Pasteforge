import secrets
from datetime import datetime, UTC

import sqlalchemy as sa
from argon2 import PasswordHasher
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.pasteforge.core.config import configs
from src.pasteforge.models import Otp, OtpBlacklist
from src.pasteforge.repositories.auth import get_active_blacklist_by_email
from src.pasteforge.repositories.utils import get_or_create
from src.pasteforge.tasks import send_otp_code_email

hasher = PasswordHasher()


async def check_blacklist_for_user(db: AsyncSession, email: str) -> str | None:
    now = datetime.now(UTC)

    blacklist = await get_active_blacklist_by_email(db, email, now)

    if blacklist is None:
        return None

    if blacklist and blacklist.expires_at is None:
        return "You have been permanently blocked. if you believe this is a mistake, please contact support."

    expiration_date_time = blacklist.expires_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"You have been blocked until {expiration_date_time}"


async def generate_otp(db: AsyncSession, email: str) -> (Otp, str, str, bool, datetime):
    expires_at = datetime.now(UTC) + configs.OTP_EXPIRATION_TIME

    otp_code = f"{secrets.randbelow(1_000_000):06d}"
    hashed_code = hasher.hash(otp_code)

    obj, is_new = await get_or_create(
        db,
        Otp,
        {"hashed_code": hashed_code, "expires_at": expires_at},
        email=email
    )

    return obj, otp_code, hashed_code, is_new, expires_at


async def refresh_otp_code(db: AsyncSession, otp: Otp, hashed_otp: str, expires_at: datetime):
    stmt = sa.update(Otp).where(Otp.id == otp.id).values(
        hashed_code=hashed_otp,
        expires_at=expires_at,
        attempts=Otp.attempts + 1
    )
    await db.execute(stmt)
    await db.commit()
    await db.refresh(otp)


async def generate_and_send_otp(db: AsyncSession, email: str):
    otp_obj, otp_code, hashed_code, is_new, expires_at = await generate_otp(db, email)

    if not is_new and otp_obj.attempts >= configs.OTP_MAX_ATTEMPTS:
        await get_or_create(db, OtpBlacklist, email=email)
        message = "Too many requests. Your email has been added to the blacklist."
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)

    if not is_new:
        await refresh_otp_code(db, otp_obj, hashed_code, expires_at)

    send_otp_code_email.delay(email, otp_code)
