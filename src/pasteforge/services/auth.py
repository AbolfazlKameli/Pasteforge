from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.core.exceptions import TooManyRequestsError
from pasteforge.services.otp import OtpService
from pasteforge.services.otp_blacklist import OtpBlacklistService
from pasteforge.tasks import send_otp_code_email


class AuthService:
    def __init__(self, db: AsyncSession):
        self.otp_blacklist_service = OtpBlacklistService(db)
        self.otp_service = OtpService(db)
        self.db = db

    async def check_blacklist_for_user(self, email: str) -> None:
        blacklist = await self.otp_blacklist_service.get_active_blacklist_by_email(email)

        if blacklist is None:
            return

        if blacklist and blacklist.expires_at is None:
            raise TooManyRequestsError(
                "You have been permanently blocked. if you believe this is a mistake, please contact support."
            )

        now = datetime.now(UTC)
        throttle_wait = (blacklist.expires_at - now).total_seconds()
        expiration_date_time = blacklist.expires_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        raise TooManyRequestsError(f"You have been blocked until {expiration_date_time}", int(throttle_wait))

    async def handle_otp_blacklist(self, email: str):
        now = datetime.now(UTC)
        blacklist_count = await self.otp_blacklist_service.get_blacklist_count_by_email(email)
        expires_at = None
        blacklist_level = str(blacklist_count + 1)

        expiration_levels = configs.OTP_SETTINGS.BLACKLIST_EXPIRATION_TIME_LEVELS
        expiration_times = configs.OTP_SETTINGS.BLACKLIST_EXPIRATION_TIME

        if blacklist_level in expiration_levels:
            expires_at = now + expiration_times[blacklist_level]

        await self.otp_blacklist_service.create_blacklist(email, expires_at)

    async def generate_and_send_otp(self, email: str) -> bool | None:
        otp_code = self.otp_service.generate_otp_code()
        otp_obj, is_new = await self.otp_service.get_or_create(email, otp_code)

        if not is_new and otp_obj.attempts >= configs.OTP_SETTINGS.MAX_ATTEMPTS:
            await self.handle_otp_blacklist(email)
            await self.otp_service.reset_otp_attempts(otp_obj)
            await self.db.commit()  # Avoiding rollback after rate limit exception
            raise TooManyRequestsError("Too many requests. Your email been added to the blacklist.")
        elif not is_new:
            await self.otp_service.refresh_otp(otp_obj, otp_code)

        send_otp_code_email.delay(email, otp_code)
