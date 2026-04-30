"""add job_results s3_key

Revision ID: 7c3d0e8f9a21
Revises: ef19fc4e3644
Create Date: 2026-04-19 15:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c3d0e8f9a21'
down_revision: Union[str, Sequence[str], None] = 'ef19fc4e3644'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('job_results', sa.Column('s3_key', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('job_results', 's3_key')