"""Add Workspace and Graph models

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
    # Create workspaces table
    op.create_table('workspaces',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspaces_owner_id'), 'workspaces', ['owner_id'], unique=False)
    
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
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_template', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'name', name='uq_workspace_graph_name')
    )
    op.create_index(op.f('ix_graphs_user_id'), 'graphs', ['user_id'], unique=False)
    op.create_index(op.f('ix_graphs_workspace_id'), 'graphs', ['workspace_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_graphs_workspace_id'), table_name='graphs')
    op.drop_index(op.f('ix_graphs_user_id'), table_name='graphs')
    op.drop_table('graphs')
    op.drop_index(op.f('ix_workspaces_owner_id'), table_name='workspaces')
    op.drop_table('workspaces')
