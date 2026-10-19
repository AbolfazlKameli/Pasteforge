from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from pasteforge.db.database import Base


class Otp(Base):
    __tablename__ = "otp"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(length=255), nullable=False, unique=True)
    hashed_code: Mapped[str] = mapped_column(String(length=128), nullable=False)
    attempts: Mapped[int] = mapped_column(default=1, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    def __repr__(self):
        return f"{self.id}, {self.email}, {self.hashed_code}, {self.attempts}, {self.expires_at}"

    def __str__(self):
        return f"{self.email} - {self.attempts} - {self.expires_at}"
