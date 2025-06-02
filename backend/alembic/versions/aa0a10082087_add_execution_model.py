"""Add Execution model

Revision ID: aa0a10082087
Revises: ab7750890da3
Create Date: 2025-06-02 14:27:21.377845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa0a10082087'
down_revision: Union[str, None] = 'ab7750890da3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create executions table
    op.create_table('executions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('graph_id', sa.String(length=36), nullable=False),
        sa.Column('trigger_message_id', sa.String(length=36), nullable=True),
        sa.Column('execution_name', sa.String(length=200), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('execution_config', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('output_logs', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('is_cancelled', sa.Boolean(), nullable=False),
        sa.Column('cancellation_reason', sa.String(length=500), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=False),
        sa.Column('current_step', sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(['graph_id'], ['graphs.id'], ),
        sa.ForeignKeyConstraint(['trigger_message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_executions_graph_id'), 'executions', ['graph_id'], unique=False)
    op.create_index(op.f('ix_executions_trigger_message_id'), 'executions', ['trigger_message_id'], unique=False)
    
    # For SQLite, we need to use batch mode to add foreign key constraints
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_messages_execution_id', 'executions', ['execution_id'], ['id'])


def downgrade() -> None:
    # Remove foreign key constraint from messages table using batch mode
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_constraint('fk_messages_execution_id', type_='foreignkey')
    
    # Drop executions table
    op.drop_index(op.f('ix_executions_trigger_message_id'), table_name='executions')
    op.drop_index(op.f('ix_executions_graph_id'), table_name='executions')
    op.drop_table('executions')
