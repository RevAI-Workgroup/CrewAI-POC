"""Add Thread model

Revision ID: 1e169d315020
Revises: 070860b1bce9
Create Date: 2025-06-02 14:35:12.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e169d315020'
down_revision: Union[str, None] = '070860b1bce9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create threads table
    op.create_table('threads',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('graph_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('thread_config', sa.JSON(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['graph_id'], ['graphs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_threads_graph_id'), 'threads', ['graph_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_threads_graph_id'), table_name='threads')
    op.drop_table('threads')
