import uuid
from datetime import datetime, UTC

import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped

from pasteforge.db.database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(sa.String(length=255), unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=datetime.now(UTC))

    def __repr__(self):
        return f"User({self.id}, {self.email}, {self.password}, {self.is_active}, {self.created_at}, {self.updated_at})"

    def __str__(self):
        return f"{self.id} - {self.email} - {self.is_active}"
