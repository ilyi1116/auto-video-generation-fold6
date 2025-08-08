"""Merge database schema revisions

Revision ID: 4b3a8cd524fa
Revises: 001, 35e042c8139d
Create Date: 2025-08-08 15:09:26.654543

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b3a8cd524fa"
down_revision: Union[str, None] = ("001", "35e042c8139d")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """執行升級遷移"""
    pass


def downgrade() -> None:
    """執行降級遷移"""
    pass
