"""add expires_at, pause_start_time, and total_paused_duration to pomodoro_sessions

Revision ID: 36d27d644fbe
Revises: 1494d893a4ce
Create Date: 2025-08-16 23:08:10.984219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36d27d644fbe'
down_revision: Union[str, Sequence[str], None] = '1494d893a4ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("pomodoro_sessions", schema=None) as batch_op:
        batch_op.add_column(sa.Column('expires_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('pause_start_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('total_paused_duration', sa.Interval(), nullable=True))

    op.execute("UPDATE pomodoro_sessions SET total_paused_duration = '0 seconds'")

    with op.batch_alter_table("pomodoro_sessions", schema=None) as batch_op:
        batch_op.alter_column('total_paused_duration',
                              existing_type=sa.Interval(),
                              nullable=False,
                              existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("pomodoro_sessions", schema=None) as batch_op:
        batch_op.drop_column('total_paused_duration')
        batch_op.drop_column('pause_start_time')
        batch_op.drop_column('expires_at')
