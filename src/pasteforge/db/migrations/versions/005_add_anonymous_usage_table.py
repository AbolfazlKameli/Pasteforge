"""005 add anonymous usage table

Revision ID: d34f4a2af5b7
Revises: 351a252413f8
Create Date: 2026-11-07 18:36:05.139569

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d34f4a2af5b7"
down_revision: str | Sequence[str] | None = "351a252413f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "anon_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hashed_ip", sa.String(length=64), nullable=False),
        sa.Column("counter", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hashed_ip"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("anon_usage")
