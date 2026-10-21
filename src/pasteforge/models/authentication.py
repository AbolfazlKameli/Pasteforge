from datetime import datetime, UTC

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.pasteforge.db.database import Base

hasher = PasswordHasher()


class Otp(Base):
    __tablename__ = 'otp'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(length=255), nullable=False, unique=True)
    hashed_code: Mapped[str] = mapped_column(String(length=128), nullable=False)
    attempts: Mapped[int] = mapped_column(default=1, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    def __repr__(self):
        return f'Otp({self.id}, {self.email}, {self.hashed_code}, {self.attempts}, {self.expires_at})'

    def __str__(self):
        return f'{self.email} - {self.attempts} - {self.expires_at}'

    def set_code(self, otp_code: str) -> None:
        self.hashed_code = hasher.hash(otp_code)

    def verify_otp(self, otp_code: str) -> bool:
        now = datetime.now(UTC)

        if self.expires_at < now:
            return False

        try:
            hasher.verify(self.hashed_code, otp_code)
            return True
        except VerifyMismatchError:
            return False


class OtpBlacklist(Base):
    __tablename__ = 'otp_blacklist'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(length=50), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=True)

    def __repr__(self):
        return f'OtpBlacklist({self.id}, {self.email}, {self.expires_at})'

    def __str__(self):
        return f'{self.id} - {self.email} - {self.expires_at}'


class RefreshTokenBlacklist(Base):
    __tablename__ = 'refresh_token_blacklist'

    id: Mapped[int] = mapped_column(primary_key=True)
    refresh: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self):
        return f'RefreshTokenBlacklist({self.id}, {self.refresh})'

    def __str__(self):
        return f'{self.id} - {self.refresh}'
