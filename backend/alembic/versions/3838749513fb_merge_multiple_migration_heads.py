"""Merge multiple migration heads

Revision ID: 3838749513fb
Revises: b3f4c5d6e7f8, e147fe9936d2
Create Date: 2025-06-16 12:41:29.208823

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3838749513fb'
down_revision: Union[str, None] = ('b3f4c5d6e7f8', 'e147fe9936d2') #type: ignore
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
