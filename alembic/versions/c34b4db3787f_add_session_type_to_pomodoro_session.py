"""add session_type to pomodoro_session

Revision ID: c34b4db3787f
Revises: 36d27d644fbe
Create Date: 2025-08-18 00:11:57.979313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c34b4db3787f'
down_revision: Union[str, Sequence[str], None] = '36d27d644fbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('pomodoro_sessions', sa.Column('session_type', sa.String(), nullable=False, server_default='work'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('pomodoro_sessions', 'session_type')
