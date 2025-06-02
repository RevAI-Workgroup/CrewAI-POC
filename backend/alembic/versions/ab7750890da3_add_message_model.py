"""Add Message model

Revision ID: ab7750890da3
Revises: 1e169d315020
Create Date: 2025-06-02 14:20:41.640955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab7750890da3'
down_revision: Union[str, None] = '1e169d315020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('thread_id', sa.String(length=36), nullable=False),
        sa.Column('execution_id', sa.String(length=36), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('message_metadata', sa.JSON(), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('triggers_execution', sa.Boolean(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_execution_id'), 'messages', ['execution_id'], unique=False)
    op.create_index(op.f('ix_messages_thread_id'), 'messages', ['thread_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_messages_thread_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_execution_id'), table_name='messages')
    op.drop_table('messages')
