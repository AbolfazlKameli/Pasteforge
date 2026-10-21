import logging
import secrets
import uuid
from datetime import datetime, UTC, timedelta
from typing import Literal, Annotated

import sqlalchemy as sa
from argon2 import PasswordHasher
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.pasteforge.core.config import configs
from src.pasteforge.models import Otp, OtpBlacklist, User
from src.pasteforge.repositories.auth import (
    create_otp,
    get_active_blacklist_by_email,
    get_otp,
    get_user_blacklist_count,
    reset_otp_attempts
)
from src.pasteforge.repositories.users import get_user_by_email
from src.pasteforge.tasks.auth import send_otp_code_email

hasher = PasswordHasher()
logger = logging.getLogger(__name__)


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme.")

            try:
                decode_access_token(credentials.credentials)
            except JWTError as e:
                raise e

            return credentials.credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )


oauth_schema = JWTBearer(auto_error=False)


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


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)

    if user is None:
        return None

    if not user.is_active:
        return None

    if not user.verify_password(password):
        return None

    return user


def create_jwt_token(
        user_id: uuid.UUID,
        email: str,
        token_type: Literal["access", "refresh"],
        expires_at: timedelta = timedelta(minutes=15)
) -> str:
    payload = {"user_id": str(user_id), "email": email, "token_type": token_type}
    exp = datetime.now(UTC) + expires_at
    payload.update({"exp": exp})
    return jwt.encode(payload, configs.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: Annotated[str, Depends(oauth_schema)]):
    try:
        payload = jwt.decode(token, configs.SECRET_KEY, algorithms=["HS256"])
        user_id: uuid.UUID = uuid.UUID(payload.get("user_id"))
        token_type: str = payload.get("token_type")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, Invalid token.",
            )

        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, invalid token type."
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, invalid or expired token.",
        )

    return user_id


def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(token, configs.SECRET_KEY, algorithms=["HS256"])
        user_id: uuid.UUID = uuid.UUID(payload.get("user_id"))
        token_type: str = payload.get("token_type")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, Invalid token.",
            )

        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, invalid token type."
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, invalid or expired token.",
        )

    return user_id
