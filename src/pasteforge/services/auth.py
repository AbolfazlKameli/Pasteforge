from datetime import datetime, UTC

from sqlalchemy.ext.asyncio import AsyncSession

from src.pasteforge.repositories.auth import get_active_blacklist_by_email


async def check_blacklist_for_user(db: AsyncSession, email: str) -> str | None:
    now = datetime.now(UTC)

    blacklist = await get_active_blacklist_by_email(db, email, now)

    if blacklist is None:
        return None

    if blacklist and blacklist.expires_at is None:
        return "You have been permanently blocked. if you believe this is a mistake, please contact support."

    expiration_date_time = blacklist.expires_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"You have been blocked until {expiration_date_time}"
