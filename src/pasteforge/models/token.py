import uuid
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pasteforge.db.database import Base
from pasteforge.models.users import User


class TokenPairStatuses(Enum):
    active = "active"
    blacklisted = "blacklisted"


class TokenObtainPair(Base):
    __tablename__ = "token_obtain_pair"

    id: Mapped[int] = mapped_column(primary_key=True)
    sid: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), unique=True)
    status: Mapped[TokenPairStatuses] = mapped_column(
        sa.Enum(TokenPairStatuses, name="token_pair_statuses_enum"),
        default=TokenPairStatuses.active,
        nullable=False,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    owner: Mapped[User] = relationship()

    def __repr__(self):
        return f"TokenObtainPair({self.id}, {self.sid}, {self.status}, {self.owner})"

    def __str__(self):
        return f"{self.id} - {self.sid} - {self.owner} - {self.status}"
