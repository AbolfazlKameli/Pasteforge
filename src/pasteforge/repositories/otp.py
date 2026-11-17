from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.models import Otp


class OtpRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str, *, for_update: bool = False) -> Otp | None:
        stmt = select(Otp).where(Otp.email == email)

        if for_update:
            stmt = stmt.with_for_update()

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_if_not_exists(self, email: str, hashed_code: str, expires_at: datetime) -> tuple[Otp, bool]:
        stmt = (
            insert(Otp)
            .values(email=email, hashed_code=hashed_code, expires_at=expires_at)
            .on_conflict_do_nothing(index_elements=[Otp.email])
            .returning(Otp)
        )

        result = await self.db.execute(stmt)
        otp = result.scalar_one_or_none()

        if otp is not None:
            return otp, True

        otp = await self.get_by_email(email, for_update=True)
        if otp is None:
            raise RuntimeError("OTP creation conflict without an existing record.")

        return otp, False

    async def refresh_otp(self, otp_id: int, hashed_code: str, expires_at: datetime) -> None:
        stmt = (
            update(Otp)
            .where(Otp.id == otp_id, Otp.attempts < configs.OTP_SETTINGS.MAX_ATTEMPTS)
            .values(hashed_code=hashed_code, expires_at=expires_at, attempts=Otp.attempts + 1)
        )

        await self.db.execute(stmt)

    async def delete(self, otp: Otp) -> None:
        await self.db.delete(otp)
        await self.db.flush()

    async def reset_attempts(self, otp: Otp) -> None:
        otp.attempts = 0
        await self.db.flush()
