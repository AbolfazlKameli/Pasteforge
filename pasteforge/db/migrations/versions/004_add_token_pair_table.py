"""004 add token pair table

Revision ID: 351a252413f8
Revises: a34a4110687a
Create Date: 2026-11-07 18:35:18.958819

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "351a252413f8"
down_revision: str | Sequence[str] | None = "a34a4110687a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "token_obtain_pair",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sid", sa.UUID(), nullable=False),
        sa.Column("status", sa.Enum("active", "blacklisted", name="token_pair_statuses_enum"), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sid"),
    )
    op.create_index(op.f("ix_token_obtain_pair_owner_id"), "token_obtain_pair", ["owner_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_token_obtain_pair_owner_id"), table_name="token_obtain_pair")
    op.drop_table("token_obtain_pair")
