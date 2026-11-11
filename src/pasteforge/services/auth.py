from datetime import UTC, datetime
from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.core.exceptions import TooManyRequestsError
from pasteforge.services.otp import OtpService
from pasteforge.services.otp_blacklist import OtpBlacklistService
from pasteforge.tasks import send_otp_code_email


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.otp_service = OtpService(db)
        self.otp_blacklist_service = OtpBlacklistService(db)

    async def check_blacklist_for_user(self, email: str) -> None:
        blacklist = await self.otp_blacklist_service.get_active_by_email(email)

        if blacklist is None:
            return

        if blacklist.expires_at is None:
            raise TooManyRequestsError(
                "You have been permanently blocked. If you believe this is a mistake, please contact support."
            )

        now = datetime.now(UTC)
        remaining_seconds = max(1, ceil((blacklist.expires_at - now).total_seconds()))

        expiration = blacklist.expires_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

        raise TooManyRequestsError(f"You have been blocked until {expiration}.", remaining_seconds)

    async def handle_otp_blacklist(self, email: str) -> None:
        blacklist_count = await self.otp_blacklist_service.count_by_email(email)

        level = str(blacklist_count + 1)

        expiration_levels = configs.OTP_SETTINGS.BLACKLIST_EXPIRATION_TIME_LEVELS
        expiration_times = configs.OTP_SETTINGS.BLACKLIST_EXPIRATION_TIME

        expires_at = None
        if level in expiration_levels:
            expires_at = datetime.now(UTC) + expiration_times[level]

        await self.otp_blacklist_service.create(email=email, expires_at=expires_at)

    async def generate_and_send_otp(self, email: str) -> None:
        otp_code = self.otp_service.generate_otp_code()
        otp_obj, is_new = await self.otp_service.get_or_create(email=email, otp_code=otp_code)

        if not is_new and otp_obj.attempts >= configs.OTP_SETTINGS.MAX_ATTEMPTS:
            await self.handle_otp_blacklist(email)
            await self.otp_service.reset_otp_attempts(otp_obj)
            # Persist blacklist and reset before raising the rate-limit error.
            await self.db.commit()
            raise TooManyRequestsError("Too many requests. Your email has been added to the blacklist.")

        if not is_new:
            await self.otp_service.refresh_otp(otp_obj, otp_code)

        # Persist the OTP before dispatching the email task.
        await self.db.commit()

        send_otp_code_email.delay(email, otp_code)
