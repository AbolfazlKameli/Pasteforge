import enum
import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from pasteforge.db.database import Base


class IdempotencyStatus(enum.Enum):
    processing = "processing"
    completed = "completed"


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    __table_args__ = (
        sa.CheckConstraint(
            """
            (status = 'processing' AND response_status IS NULL AND response_body IS NULL)
            OR
            (status = 'completed' AND response_status IS NOT NULL AND response_body IS NOT NULL)
            """,
            name="ck_idempotency_response_state",
        ),
        sa.UniqueConstraint("scope_key", "key", name="uq_idempotency_scope_key"),
    )
    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope_key: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    key: Mapped[uuid.UUID] = mapped_column(sa.Uuid(as_uuid=True), nullable=False)
    request_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    status: Mapped[IdempotencyStatus] = mapped_column(
        sa.Enum(IdempotencyStatus, name="idempotency_status"),
        nullable=False,
        default=IdempotencyStatus.processing,
    )
    response_status: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    response_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
