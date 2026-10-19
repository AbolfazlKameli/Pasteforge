"""create otp_blacklist table

Revision ID: 0bf8fc13c34e
Revises: 9ebcf6f56503
Create Date: 2026-10-19 21:19:49.317163

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0bf8fc13c34e'
down_revision: Union[str, Sequence[str], None] = '9ebcf6f56503'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "otp_blacklist",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(length=50), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("otp_blacklist")
