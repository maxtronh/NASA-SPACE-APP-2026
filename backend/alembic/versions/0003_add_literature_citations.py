"""0003_add_literature_citations

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-12 19:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: str | None = '0002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'literature_citations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('investigation_id', sa.Uuid(), nullable=False),
        sa.Column('doi', sa.String(length=100), nullable=True),
        sa.Column('ntrs_id', sa.String(length=50), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('authors', sa.JSON(), nullable=False),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('journal_or_book', sa.String(length=255), nullable=True),
        sa.Column('bibtex', sa.Text(), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='VERIFIED_CROSSREF'),
        sa.Column('sha256_checksum', sa.String(length=64), nullable=False),
        sa.Column('raw_metadata', sa.JSON(), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_literature_citations_investigation_id', 'literature_citations', ['investigation_id'], unique=False)
    op.create_index('ix_literature_citations_doi', 'literature_citations', ['doi'], unique=False)
    op.create_index('ix_literature_citations_ntrs_id', 'literature_citations', ['ntrs_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_literature_citations_ntrs_id', table_name='literature_citations')
    op.drop_index('ix_literature_citations_doi', table_name='literature_citations')
    op.drop_index('ix_literature_citations_investigation_id', table_name='literature_citations')
    op.drop_table('literature_citations')
