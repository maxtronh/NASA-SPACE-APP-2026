"""0002_add_hnsw_vector_index

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12 20:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'vector_embeddings' 
                    AND column_name = 'embedding' 
                    AND data_type IN ('json', 'jsonb')
                ) THEN
                    ALTER TABLE vector_embeddings 
                    ALTER COLUMN embedding TYPE vector(384) 
                    USING embedding::text::vector(384);
                END IF;
            END $$;
        """)
        op.execute("""
            CREATE INDEX IF NOT EXISTS ix_vector_embeddings_hnsw_cosine
            ON vector_embeddings
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_vector_embeddings_hnsw_cosine;")
