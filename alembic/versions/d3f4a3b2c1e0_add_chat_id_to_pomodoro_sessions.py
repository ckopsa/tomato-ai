"""add_chat_id_to_pomodoro_sessions

Revision ID: d3f4a3b2c1e0
Revises: 0e5a03fdd37f
Create Date: 2025-08-19 21:01:00.407697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3f4a3b2c1e0'
down_revision: Union[str, None] = '0e5a03fdd37f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("pomodoro_sessions", schema=None) as batch_op:
        batch_op.add_column(sa.Column('chat_id', sa.Integer(), nullable=True))

    op.execute('UPDATE pomodoro_sessions SET chat_id = 0')

    with op.batch_alter_table("pomodoro_sessions", schema=None) as batch_op:
        batch_op.alter_column('chat_id',
                              existing_type=sa.Integer(),
                              nullable=False,
                              server_default='0')


def downgrade() -> None:
    with op.batch_alter_table("pomodoro_sessions", schema=None) as batch_op:
        batch_op.drop_column('chat_id')
