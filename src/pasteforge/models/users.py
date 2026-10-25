import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pasteforge.core.config import configs
from pasteforge.db.database import Base

pwd_hasher = PasswordHasher()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(sa.String(length=255), unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    pastes: Mapped[list["Paste"]] = relationship(  # noqa: F821
        back_populates="owner",
        cascade="all",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"User({self.id}, {self.email}, {self.is_active}, {self.created_at}, {self.updated_at})"

    def __str__(self):
        return f"{self.id} - {self.email} - {self.is_active}"

    def verify_password(self, plain_password: str) -> bool:
        if self.password.startswith(configs.UNUSABLE_PASSWORD_MARKER):
            return False
        try:
            return pwd_hasher.verify(self.password, plain_password)
        except VerifyMismatchError:
            return False

    def set_password(self, plain_password: str) -> None:
        self.password = pwd_hasher.hash(plain_password)

    def set_unusable_password(self):
        self.password = configs.UNUSABLE_PASSWORD_MARKER
