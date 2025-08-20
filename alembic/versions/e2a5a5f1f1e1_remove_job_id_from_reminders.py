"""remove job_id from reminders

Revision ID: e2a5a5f1f1e1
Revises: 0e5a03fdd37f
Create Date: 2024-07-26 14:30:30.548329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2a5a5f1f1e1'
down_revision: Union[str, None] = '0e5a03fdd37f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('reminders', 'job_id')


def downgrade() -> None:
    op.add_column('reminders', sa.Column('job_id', sa.VARCHAR(), autoincrement=False, nullable=False))
