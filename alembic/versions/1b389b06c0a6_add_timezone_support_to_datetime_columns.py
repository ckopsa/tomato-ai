"""add timezone support to datetime columns

Revision ID: 1b389b06c0a6
Revises: 2ae89849827e
Create Date: 2025-08-20 07:08:31.313027

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1b389b06c0a6'
down_revision: Union[str, Sequence[str], None] = '2ae89849827e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("pomodoro_sessions", schema=None) as batch_op:
        batch_op.alter_column('start_time',
                              existing_type=postgresql.TIMESTAMP(),
                              type_=sa.DateTime(timezone=True),
                              existing_nullable=True)
        batch_op.alter_column('end_time',
                              existing_type=postgresql.TIMESTAMP(),
                              type_=sa.DateTime(timezone=True),
                              existing_nullable=True)
        batch_op.alter_column('expires_at',
                              existing_type=postgresql.TIMESTAMP(),
                              type_=sa.DateTime(timezone=True),
                              existing_nullable=True)
        batch_op.alter_column('pause_start_time',
                              existing_type=postgresql.TIMESTAMP(),
                              type_=sa.DateTime(timezone=True),
                              existing_nullable=True)

    with op.batch_alter_table("reminders", schema=None) as batch_op:
        batch_op.alter_column('created_at',
                              existing_type=postgresql.TIMESTAMP(),
                              type_=sa.DateTime(timezone=True),
                              existing_nullable=False)
        batch_op.alter_column('send_at',
                              existing_type=postgresql.TIMESTAMP(),
                              type_=sa.DateTime(timezone=True),
                              existing_nullable=True)
        batch_op.alter_column('triggered_at',
                              existing_type=postgresql.TIMESTAMP(),
                              type_=sa.DateTime(timezone=True),
                              existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("reminders", schema=None) as batch_op:
        batch_op.alter_column('triggered_at',
                              existing_type=sa.DateTime(timezone=True),
                              type_=postgresql.TIMESTAMP(),
                              existing_nullable=True)
        batch_op.alter_column('send_at',
                              existing_type=sa.DateTime(timezone=True),
                              type_=postgresql.TIMESTAMP(),
                              existing_nullable=True)
        batch_op.alter_column('created_at',
                              existing_type=sa.DateTime(timezone=True),
                              type_=postgresql.TIMESTAMP(),
                              existing_nullable=False)

    with op.batch_alter_table("pomodoro_sessions", schema=None) as batch_op:
        batch_op.alter_column('pause_start_time',
                              existing_type=sa.DateTime(timezone=True),
                              type_=postgresql.TIMESTAMP(),
                              existing_nullable=True)
        batch_op.alter_column('expires_at',
                              existing_type=sa.DateTime(timezone=True),
                              type_=postgresql.TIMESTAMP(),
                              existing_nullable=True)
        batch_op.alter_column('end_time',
                              existing_type=sa.DateTime(timezone=True),
                              type_=postgresql.TIMESTAMP(),
                              existing_nullable=True)
        batch_op.alter_column('start_time',
                              existing_type=sa.DateTime(timezone=True),
                              type_=postgresql.TIMESTAMP(),
                              existing_nullable=True)
