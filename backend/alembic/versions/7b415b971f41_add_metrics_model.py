"""Add Metrics model

Revision ID: 7b415b971f41
Revises: aa0a10082087
Create Date: 2025-06-02 15:18:24.704093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b415b971f41'
down_revision: Union[str, None] = 'aa0a10082087'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create metrics table
    op.create_table('metrics',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('execution_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('metric_name', sa.String(length=200), nullable=False),
        sa.Column('metric_type', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=20), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('step', sa.Integer(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('metric_metadata', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_aggregated', sa.Boolean(), nullable=False),
        sa.Column('aggregation_method', sa.String(length=20), nullable=True),
        sa.Column('aggregation_window', sa.String(length=50), nullable=True),
        sa.Column('mlflow_run_id', sa.String(length=100), nullable=True),
        sa.Column('mlflow_experiment_id', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['executions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_metrics_execution_id'), 'metrics', ['execution_id'], unique=False)
    op.create_index(op.f('ix_metrics_user_id'), 'metrics', ['user_id'], unique=False)
    op.create_index(op.f('ix_metrics_metric_name'), 'metrics', ['metric_name'], unique=False)
    op.create_index(op.f('ix_metrics_timestamp'), 'metrics', ['timestamp'], unique=False)
    op.create_index(op.f('ix_metrics_mlflow_run_id'), 'metrics', ['mlflow_run_id'], unique=False)
    op.create_index('idx_metrics_execution_name', 'metrics', ['execution_id', 'metric_name'], unique=False)
    op.create_index('idx_metrics_timestamp_type', 'metrics', ['timestamp', 'metric_type'], unique=False)
    op.create_index('idx_metrics_category_name', 'metrics', ['category', 'metric_name'], unique=False)
    op.create_index('idx_metrics_mlflow_run', 'metrics', ['mlflow_run_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_metrics_mlflow_run', table_name='metrics')
    op.drop_index('idx_metrics_category_name', table_name='metrics')
    op.drop_index('idx_metrics_timestamp_type', table_name='metrics')
    op.drop_index('idx_metrics_execution_name', table_name='metrics')
    op.drop_index(op.f('ix_metrics_mlflow_run_id'), table_name='metrics')
    op.drop_index(op.f('ix_metrics_timestamp'), table_name='metrics')
    op.drop_index(op.f('ix_metrics_metric_name'), table_name='metrics')
    op.drop_index(op.f('ix_metrics_user_id'), table_name='metrics')
    op.drop_index(op.f('ix_metrics_execution_id'), table_name='metrics')
    
    # Drop table
    op.drop_table('metrics')
