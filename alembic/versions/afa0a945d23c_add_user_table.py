"""add user table

Revision ID: afa0a945d23c
Revises: a16f4c7d08a6
Create Date: 2025-08-21 17:44:08.780429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afa0a945d23c'
down_revision: Union[str, Sequence[str], None] = 'a16f4c7d08a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('telegram_chat_id', sa.String(), nullable=False),
        sa.Column('timezone', sa.String(), server_default='UTC', nullable=False),
        sa.Column('work_start', sa.Time(), server_default='09:00:00', nullable=False),
        sa.Column('work_end', sa.Time(), server_default='17:00:00', nullable=False),
        sa.Column('desired_sessions_per_day', sa.Integer(), server_default='8', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_chat_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
