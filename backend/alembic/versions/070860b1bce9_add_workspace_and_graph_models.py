"""Add Graph model

Revision ID: 070860b1bce9
Revises: 89ab0fdbdfff
Create Date: 2025-06-02 14:01:38.323914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '070860b1bce9'
down_revision: Union[str, None] = '89ab0fdbdfff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create graphs table
    op.create_table('graphs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('graph_data', sa.JSON(), nullable=False),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_template', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_graph_name')
    )
    op.create_index(op.f('ix_graphs_user_id'), 'graphs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_graphs_user_id'), table_name='graphs')
    op.drop_table('graphs')
