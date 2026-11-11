import secrets
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.core.exceptions import ForbiddenError
from pasteforge.core.security import hash_value, validate_value
from pasteforge.models import Otp
from pasteforge.repositories import OtpRepository


class OtpService:
    def __init__(self, db: AsyncSession) -> None:
        self.otp_repo = OtpRepository(db)

    @staticmethod
    def generate_otp_code() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def _get_expiration_time() -> datetime:
        return datetime.now(UTC) + configs.OTP_SETTINGS.EXPIRATION_TIME

    async def get_otp_by_email(self, email: str, *, for_update: bool = False) -> Otp | None:
        return await self.otp_repo.get_by_email(email, for_update=for_update)

    async def validate_otp(self, email: str, otp_code: str) -> Otp:
        otp = await self.get_otp_by_email(email)

        if otp is None or otp.expires_at <= datetime.now(UTC) or not validate_value(otp.hashed_code, otp_code):
            raise ForbiddenError("Invalid or expired OTP code.")

        return otp

    async def get_or_create(self, email: str, otp_code: str) -> tuple[Otp, bool]:
        return await self.otp_repo.create_if_not_exists(
            email=email, hashed_code=hash_value(otp_code), expires_at=self._get_expiration_time()
        )

    async def refresh_otp(self, otp: Otp, otp_code: str) -> None:
        await self.otp_repo.refresh_otp(
            otp_id=otp.id, hashed_code=hash_value(otp_code), expires_at=self._get_expiration_time()
        )

    async def delete_otp(self, otp: Otp) -> None:
        await self.otp_repo.delete(otp)

    async def reset_otp_attempts(self, otp: Otp) -> None:
        await self.otp_repo.reset_attempts(otp)
