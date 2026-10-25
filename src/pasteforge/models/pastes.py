import uuid
from datetime import UTC, datetime
from enum import Enum

import sqlalchemy as sa
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pasteforge.core.config import configs
from pasteforge.db.database import Base

pwd_hasher = PasswordHasher()


class PastesAccessTypes(Enum):
    public = "public"
    private = "private"
    password_protected = "password_protected"


class Paste(Base):
    __tablename__ = "pastes"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    syntax: Mapped[str | None] = mapped_column(sa.String(length=50), nullable=True)
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False)
    access_type: Mapped[PastesAccessTypes] = mapped_column(
        sa.Enum(PastesAccessTypes, name="pastes_access_types_enum"),
        default=PastesAccessTypes.public,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), default=True, nullable=False)
    password: Mapped[str | None] = mapped_column(sa.String(), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    owner: Mapped["User | None"] = relationship(back_populates="pastes")  # noqa: F821

    def __repr__(self):
        return f"Paste({self.id}, {self.is_active}, {self.created_at})"

    def __str__(self):
        return f"{self.id} - {self.is_active}"

    def verify_password(self, plain_password: str) -> bool:
        if self.password.startswith(configs.UNUSABLE_PASSWORD_MARKER):
            return False
        try:
            return pwd_hasher.verify(self.password, plain_password)
        except VerifyMismatchError:
            return False

    def set_password(self, plain_password: str) -> None:
        self.password = pwd_hasher.hash(plain_password)
