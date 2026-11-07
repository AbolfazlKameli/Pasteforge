import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from pasteforge.db.database import Base


class AnonymousUsage(Base):
    __tablename__ = "anon_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    hashed_ip: Mapped[str] = mapped_column(sa.String(length=64), nullable=False)
    counter: Mapped[int] = mapped_column(sa.SmallInteger(), nullable=False, default=1)

    def __repr__(self):
        return f"AnonymousUsage({self.id}, {self.hashed_ip}, {self.counter})"

    def __str__(self):
        return f"{self.id} - {self.counter}"
