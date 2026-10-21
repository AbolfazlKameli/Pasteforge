import logging
import secrets
from datetime import datetime, UTC

import sqlalchemy as sa
from argon2 import PasswordHasher
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.pasteforge.core.config import configs
from src.pasteforge.models import Otp, OtpBlacklist
from src.pasteforge.repositories.auth import (
    create_otp,
    get_active_blacklist_by_email,
    get_otp,
    get_user_blacklist_count,
    reset_otp_attempts
)
from src.pasteforge.tasks.auth import send_otp_code_email

hasher = PasswordHasher()
logger = logging.getLogger(__name__)


async def check_blacklist_for_user(db: AsyncSession, email: str) -> tuple[str | None, int]:
    now = datetime.now(UTC)

    blacklist = await get_active_blacklist_by_email(db, email, now)

    if blacklist is None:
        return None, 0

    if blacklist and blacklist.expires_at is None:
        return "You have been permanently blocked. if you believe this is a mistake, please contact support.", 0

    throttle_wait = (blacklist.expires_at - now).total_seconds()
    expiration_date_time = blacklist.expires_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"You have been blocked until {expiration_date_time}", int(throttle_wait)


async def refresh_otp_code(db: AsyncSession, otp: Otp, otp_code: str, expires_at: datetime):
    hashed_otp = hasher.hash(otp_code)
    stmt = sa.update(Otp).where(Otp.id == otp.id, Otp.attempts <= configs.OTP_SETTINGS.MAX_ATTEMPTS).values(
        hashed_code=hashed_otp,
        expires_at=expires_at,
        attempts=Otp.attempts + 1
    )
    await db.execute(stmt)


async def handle_otp_blacklist(db: AsyncSession, email: str):
    now = datetime.now(UTC)
    blacklist_count = await get_user_blacklist_count(db, email)
    expires_at = None
    blacklist_level = str(blacklist_count + 1)

    expiration_levels = configs.OTP_SETTINGS.BLACKLIST_EXPIRATION_TIME_LEVELS
    expiration_times = configs.OTP_SETTINGS.BLACKLIST_EXPIRATION_TIME

    if blacklist_level in expiration_levels:
        expires_at = now + expiration_times[blacklist_level]

    blacklist = OtpBlacklist(email=email, expires_at=expires_at)
    db.add(blacklist)
    await db.flush()


async def generate_and_send_otp(db: AsyncSession, email: str):
    try:
        otp = await get_otp(db, email, True)

        expires_at = datetime.now(UTC) + configs.OTP_SETTINGS.EXPIRATION_TIME
        otp_code = f"{secrets.randbelow(1_000_000):06d}"
        blacklisted = False

        if otp is None:
            await create_otp(db, email, otp_code, expires_at)
        elif otp.attempts >= configs.OTP_SETTINGS.MAX_ATTEMPTS:
            await handle_otp_blacklist(db, email)
            await reset_otp_attempts(db, otp)
            blacklisted = True
        else:
            await refresh_otp_code(db, otp, otp_code, expires_at)

        await db.commit()

        if blacklisted:
            message = "Too many requests. Your email has been added to the blacklist."
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)

        send_otp_code_email.delay(email, otp_code)

    except IntegrityError:
        logger.warning("OTP persistence failed due to an integrity constraint")

        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="OTP already exists. Please retry.") from None
