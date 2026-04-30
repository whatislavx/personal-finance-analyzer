"""stub missing revision

Revision ID: d3e6bb2fea4f
Revises: 1a68a0cff557
Create Date: 2026-04-19

This file was added to восстановить целостность графа Alembic.
В БД в таблице alembic_version записан revision d3e6bb2fea4f,
но сам файл миграции отсутствовал, из-за чего любые команды alembic падали.

Миграция не выполняет никаких изменений схемы (no-op).

"""

from typing import Sequence, Union

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = "d3e6bb2fea4f"
down_revision: Union[str, Sequence[str], None] = "1a68a0cff557"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema (no-op)."""
    pass


def downgrade() -> None:
    """Downgrade schema (no-op)."""
    pass

