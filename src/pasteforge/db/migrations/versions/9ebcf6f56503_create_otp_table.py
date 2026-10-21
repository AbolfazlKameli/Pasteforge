"""create otp table

Revision ID: 9ebcf6f56503
Revises: 5a5c24106c48
Create Date: 2026-10-19 20:45:12.043874

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ebcf6f56503"
down_revision: str | Sequence[str] | None = "5a5c24106c48"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "otp",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_code", sa.String(length=128), nullable=False),
        sa.Column("attempts", sa.Integer, default=1, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("otp")
