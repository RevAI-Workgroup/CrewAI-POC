"""Add LLM to NodeTypeEnum

Revision ID: e822596fe37d
Revises: 9cd2b9bd1513
Create Date: 2025-06-03 02:38:37.473866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e822596fe37d'
down_revision: Union[str, None] = '9cd2b9bd1513'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add LLM to the NodeTypeEnum
    # PostgreSQL requires special handling for enum modifications
    op.execute("ALTER TYPE nodetypeenum ADD VALUE 'LLM'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum and all dependent objects
    # For now, we'll leave the enum value in place as it's safer
    pass
