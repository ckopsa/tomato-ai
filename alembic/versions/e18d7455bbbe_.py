"""empty message

Revision ID: e18d7455bbbe
Revises: d3f4a3b2c1e0, e2a5a5f1f1e1
Create Date: 2025-08-19 22:29:16.932455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e18d7455bbbe'
down_revision: Union[str, Sequence[str], None] = ('d3f4a3b2c1e0', 'e2a5a5f1f1e1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
