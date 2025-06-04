"""remove_unique_constraint_on_graph_name

Revision ID: a2e105ab58ba
Revises: 1baf1c9d3ae1
Create Date: 2025-06-04 12:43:27.953396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2e105ab58ba'
down_revision: Union[str, None] = '1baf1c9d3ae1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the unique constraint on user_id and name
    op.drop_constraint('uq_user_graph_name', 'graphs', type_='unique')


def downgrade() -> None:
    # Recreate the unique constraint on user_id and name
    op.create_unique_constraint('uq_user_graph_name', 'graphs', ['user_id', 'name'])
