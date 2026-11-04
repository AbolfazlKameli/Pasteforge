import secrets
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.core.exceptions import ForbiddenError
from pasteforge.core.security import hash_value, validate_value
from pasteforge.models import Otp
from pasteforge.repositories import OtpRepository


class OtpService:
    def __init__(self, db: AsyncSession):
        self.otp_repo = OtpRepository(db)

    @staticmethod
    def generate_otp_code() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    async def get_otp_by_email(self, email: str) -> Otp | None:
        return await self.otp_repo.get_by_email(email, False)

    async def get_otp_by_email_for_update(self, email: str) -> Otp | None:
        return await self.otp_repo.get_by_email(email, True)

    async def validate_otp(self, email: str, otp_code: str) -> Otp:
        otp_obj = await self.get_otp_by_email(email)
        if otp_obj is None or (not validate_value(otp_obj.hashed_code, otp_code)):
            raise ForbiddenError("Invalid or expired OTP code.")
        return otp_obj

    async def get_or_create(self, email: str, otp_code: str) -> tuple[Otp, bool]:
        otp = await self.get_otp_by_email(email)
        is_new = False

        if otp is None:
            expires_at = datetime.now(UTC) + configs.OTP_SETTINGS.EXPIRATION_TIME
            hashed_otp = hash_value(otp_code)
            otp = await self.otp_repo.create(email, hashed_otp, expires_at)
            is_new = True

        return otp, is_new

    async def refresh_otp(self, otp: Otp, otp_code: str) -> None:
        expires_at = datetime.now(UTC) + configs.OTP_SETTINGS.EXPIRATION_TIME
        hashed_otp = hash_value(otp_code)
        await self.otp_repo.update_expired(otp.id, hashed_otp, expires_at)

    async def delete_otp(self, otp: Otp) -> None:
        await self.otp_repo.delete(otp)

    async def reset_otp_attempts(self, otp: Otp) -> None:
        await self.otp_repo.reset_attempts(otp)
