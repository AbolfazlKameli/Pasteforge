"""006 add pastes table

Revision ID: b9bef2b18b67
Revises: d34f4a2af5b7
Create Date: 2026-11-07 18:36:42.244191

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b9bef2b18b67"
down_revision: str | Sequence[str] | None = "d34f4a2af5b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "pastes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("syntax", sa.String(length=50), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "access_type",
            sa.Enum("public", "private", "password_protected", name="pastes_access_types_enum"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("password", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], onupdate="CASCADE", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pastes_expires_at"), "pastes", ["expires_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_pastes_expires_at"), table_name="pastes")
    op.drop_table("pastes")
