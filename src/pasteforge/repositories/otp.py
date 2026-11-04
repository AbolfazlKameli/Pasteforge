from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.models import Otp


class OtpRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str, for_update: bool = False) -> Otp | None:
        stmt = sa.select(Otp).where(Otp.email == email)

        if for_update:
            stmt = stmt.with_for_update()

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, email: str, hashed_code: str, expires_at: datetime) -> Otp:
        otp = Otp(email=email, expires_at=expires_at, hashed_code=hashed_code)
        self.db.add(otp)
        await self.db.flush()
        await self.db.refresh(otp)
        return otp

    async def update_expired(self, otp_id: int, hashed_code: str, expires_at: datetime) -> None:
        stmt = (
            sa.update(Otp)
            .where(Otp.id == otp_id, Otp.attempts <= configs.OTP_SETTINGS.MAX_ATTEMPTS)
            .values(hashed_code=hashed_code, expires_at=expires_at, attempts=Otp.attempts + 1)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def delete(self, otp: Otp) -> None:
        await self.db.delete(otp)
        await self.db.flush()

    async def reset_attempts(self, otp: Otp) -> None:
        await self.db.execute(sa.update(Otp).where(Otp.id == otp.id).values(attempts=0))
