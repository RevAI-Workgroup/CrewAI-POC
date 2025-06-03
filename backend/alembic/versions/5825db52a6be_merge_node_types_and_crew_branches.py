"""Merge node types and crew branches

Revision ID: 5825db52a6be
Revises: 9362a4f8e515, e147fe9936d2
Create Date: 2025-06-03 02:37:04.186313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5825db52a6be'
down_revision: Union[str, None] = ('9362a4f8e515', 'e147fe9936d2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
