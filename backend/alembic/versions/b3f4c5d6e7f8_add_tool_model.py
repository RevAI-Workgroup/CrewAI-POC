"""add_tool_model

Revision ID: b3f4c5d6e7f8
Revises: a2e105ab58ba
Create Date: 2024-01-20 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b3f4c5d6e7f8'
down_revision: Union[str, None] = 'a2e105ab58ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tools table
    op.create_table('tools',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('schema', sa.JSON(), nullable=False),
        sa.Column('implementation', sa.Text(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('is_public', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_tools_id'), 'tools', ['id'], unique=False)
    op.create_index(op.f('ix_tools_name'), 'tools', ['name'], unique=False)
    op.create_index(op.f('ix_tools_category'), 'tools', ['category'], unique=False)
    op.create_index(op.f('ix_tools_user_id'), 'tools', ['user_id'], unique=False)
    op.create_index('idx_tool_name_user', 'tools', ['name', 'user_id'], unique=False)
    op.create_index('idx_tool_category', 'tools', ['category'], unique=False)
    op.create_index('idx_tool_public', 'tools', ['is_public'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_tool_public', table_name='tools')
    op.drop_index('idx_tool_category', table_name='tools')
    op.drop_index('idx_tool_name_user', table_name='tools')
    op.drop_index(op.f('ix_tools_user_id'), table_name='tools')
    op.drop_index(op.f('ix_tools_category'), table_name='tools')
    op.drop_index(op.f('ix_tools_name'), table_name='tools')
    op.drop_index(op.f('ix_tools_id'), table_name='tools')
    
    # Drop table
    op.drop_table('tools') 