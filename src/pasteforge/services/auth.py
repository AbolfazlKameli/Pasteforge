import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import sqlalchemy as sa
from argon2 import PasswordHasher
from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import db_dependency
from pasteforge.core.config import configs
from pasteforge.models import Otp, OtpBlacklist, TokenObtainPair, User
from pasteforge.repositories.auth import (
    create_otp,
    get_active_blacklist_by_email,
    get_blacklist_by_token,
    get_otp,
    get_user_blacklist_count,
    reset_otp_attempts,
    token_pair_exists,
)
from pasteforge.repositories.users import get_user_by_email, get_user_by_id
from pasteforge.tasks.auth import send_otp_code_email

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
    stmt = (
        sa.update(Otp)
        .where(Otp.id == otp.id, Otp.attempts <= configs.OTP_SETTINGS.MAX_ATTEMPTS)
        .values(hashed_code=hashed_otp, expires_at=expires_at, attempts=Otp.attempts + 1)
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


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)

    if user is None:
        return None

    if not user.is_active:
        return None

    if not user.verify_password(password):
        return None

    return user


def raise_auth_error(token_type: str, detail: str, e: Exception | None = None) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={
            "WWW-Authenticate": 'Bearer error="invalid_token"',
            "X-Auth-Error": f"{token_type}_token_invalid",
        },
    ) from e


async def create_token_pairs(db: AsyncSession, user_id: uuid.UUID, email: str) -> tuple[str, str]:
    access_payload = {"user_id": str(user_id), "email": email}
    access_exp = datetime.now(UTC) + timedelta(minutes=15)
    access_payload.update({"exp": access_exp, "token_type": "access"})

    refresh_payload = {"user_id": str(user_id), "email": email}
    refresh_exp = datetime.now(UTC) + timedelta(hours=24)
    refresh_payload.update({"exp": refresh_exp, "token_type": "refresh"})

    access_token = jwt.encode(access_payload, configs.SECRET_KEY, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, configs.SECRET_KEY, algorithm="HS256")

    token_pair = TokenObtainPair(refresh=refresh_token, access=access_token, owner_id=user_id)
    db.add(token_pair)
    await db.commit()

    return access_token, refresh_token


async def decode_access_token(db: AsyncSession, token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, configs.SECRET_KEY, algorithms=["HS256"])
        user_id: uuid.UUID = uuid.UUID(payload.get("user_id"))
        token_type: str = payload.get("token_type")
    except (JWTError, ValueError, TypeError, KeyError) as e:
        raise_auth_error("access", "Invalid or expired access token.", e)

    if token_type != "access":
        raise_auth_error("access", "Invalid access token type.")

    blacklist = await get_blacklist_by_token(db, token)
    if blacklist is not None:
        raise_auth_error("access", "Access token has been revoked.")

    if not await token_pair_exists(db, token):
        raise_auth_error("access", "Access token is not associated with a valid session.")

    return user_id


async def decode_refresh_token(db: AsyncSession, token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, configs.SECRET_KEY, algorithms=["HS256"])
        user_id: uuid.UUID = uuid.UUID(payload["user_id"])
        token_type: str = payload.get("token_type")
    except (JWTError, ValueError, TypeError, KeyError) as e:
        raise_auth_error("refresh", "Invalid or expired refresh token.", e)

    if token_type != "refresh":
        raise_auth_error("refresh", "Invalid refresh token type.")

    blacklist = await get_blacklist_by_token(db, token)
    if blacklist is not None:
        raise_auth_error("refresh", "Refresh token has been revoked.")

    if not await token_pair_exists(db, token):
        raise_auth_error("refresh", "Refresh token is not associated with a valid session.")

    return user_id


async def jwt_cookie(db: db_dependency, access_token: Annotated[str | None, Cookie()] = None) -> uuid.UUID:
    if not access_token:
        raise_auth_error("access", "Access token is missing.")

    return await decode_access_token(db, access_token)


async def get_authenticated_user(db: db_dependency, user_id: Annotated[uuid.UUID, Depends(jwt_cookie)]):
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, invalid user.",
        )
    return user


async def get_active_user(user: Annotated[User, Depends(get_authenticated_user)]):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")

    return user


user_dependency = Annotated[User, Depends(get_active_user)]
