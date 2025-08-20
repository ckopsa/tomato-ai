"""add send_at to reminders

Revision ID: 2ae89849827e
Revises: e18d7455bbbe
Create Date: 2025-08-20 04:38:35.642389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ae89849827e'
down_revision: Union[str, Sequence[str], None] = 'e18d7455bbbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('reminders', sa.Column('send_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reminders', 'send_at')
