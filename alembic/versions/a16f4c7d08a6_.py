"""empty message

Revision ID: a16f4c7d08a6
Revises: 1b389b06c0a6, f5e3a8b4c2d1
Create Date: 2025-08-20 22:00:37.637731

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a16f4c7d08a6'
down_revision: Union[str, Sequence[str], None] = ('1b389b06c0a6', 'f5e3a8b4c2d1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
