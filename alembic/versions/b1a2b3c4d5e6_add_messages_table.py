"""add messages table

Revision ID: b1a2b3c4d5e6
Revises: f5e3a8b4c2d1
Create Date: 2025-08-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a2b3c4d5e6'
down_revision: Union[str, None] = 'f5e3a8b4c2d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('sender', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('messages')
