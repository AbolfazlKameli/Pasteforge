"""create users table

Revision ID: 5a5c24106c48
Revises:
Create Date: 2026-10-19 18:08:24.666095

"""
import uuid
from datetime import datetime, UTC
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5a5c24106c48'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(length=255), unique=True, nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC),
                  onupdate=lambda: datetime.now(UTC))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
