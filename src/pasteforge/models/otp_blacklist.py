from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from pasteforge.db.database import Base


class OtpBlacklist(Base):
    __tablename__ = "otp_blacklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(sa.String(length=50), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=True)

    def __repr__(self):
        return f"OtpBlacklist({self.id}, {self.email}, {self.expires_at})"

    def __str__(self):
        return f"{self.id} - {self.email} - {self.expires_at}"
