"""Remove CUSTOM from LLMProviderEnum

Revision ID: ae38e2cc633b
Revises: e822596fe37d
Create Date: 2025-06-03 02:42:47.462876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae38e2cc633b'
down_revision: Union[str, None] = 'e822596fe37d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # We need to create a new enum and update the column
    
    # First, check if any rows use the CUSTOM value (there shouldn't be any)
    # If there were, we'd need to update them first
    
    # Create a new enum without CUSTOM
    op.execute("CREATE TYPE llmproviderenum_new AS ENUM ('OPENAI', 'ANTHROPIC', 'GOOGLE', 'AZURE', 'AWS_BEDROCK', 'OLLAMA', 'GROQ', 'HUGGINGFACE', 'MISTRAL', 'NVIDIA_NIM', 'FIREWORKS', 'PERPLEXITY', 'SAMBANOVA', 'CEREBRAS', 'OPENROUTER')")
    
    # Update the column to use the new enum
    op.execute("ALTER TABLE llm_nodes ALTER COLUMN provider TYPE llmproviderenum_new USING provider::text::llmproviderenum_new")
    
    # Drop the old enum
    op.execute("DROP TYPE llmproviderenum")
    
    # Rename the new enum to the original name
    op.execute("ALTER TYPE llmproviderenum_new RENAME TO llmproviderenum")


def downgrade() -> None:
    # To downgrade, we'd need to add CUSTOM back
    # Create a new enum with CUSTOM
    op.execute("CREATE TYPE llmproviderenum_new AS ENUM ('OPENAI', 'ANTHROPIC', 'GOOGLE', 'AZURE', 'AWS_BEDROCK', 'OLLAMA', 'GROQ', 'HUGGINGFACE', 'MISTRAL', 'NVIDIA_NIM', 'FIREWORKS', 'PERPLEXITY', 'SAMBANOVA', 'CEREBRAS', 'OPENROUTER', 'CUSTOM')")
    
    # Update the column to use the new enum
    op.execute("ALTER TABLE llm_nodes ALTER COLUMN provider TYPE llmproviderenum_new USING provider::text::llmproviderenum_new")
    
    # Drop the old enum
    op.execute("DROP TYPE llmproviderenum")
    
    # Rename the new enum to the original name
    op.execute("ALTER TYPE llmproviderenum_new RENAME TO llmproviderenum")
