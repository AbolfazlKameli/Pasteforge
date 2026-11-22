"""003 add otp blacklist table

Revision ID: a34a4110687a
Revises: 7dfbed573004
Create Date: 2026-11-07 18:34:42.278168

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a34a4110687a"
down_revision: str | Sequence[str] | None = "7dfbed573004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "otp_blacklist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_otp_blacklist_email"), "otp_blacklist", ["email"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_otp_blacklist_email"), table_name="otp_blacklist")
    op.drop_table("otp_blacklist")
