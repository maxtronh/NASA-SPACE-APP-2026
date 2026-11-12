"""0001_initial_schema

Revision ID: 0001
Revises: 
Create Date: 2026-11-12 18:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. investigations
    op.create_table(
        'investigations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('short_name', sa.String(length=50), nullable=False),
        sa.Column('project_acronym', sa.String(length=50), nullable=False),
        sa.Column('facility', sa.String(length=100), nullable=False),
        sa.Column('combustion_regime', sa.String(length=50), nullable=False),
        sa.Column('fuel_type', sa.String(length=100), nullable=False),
        sa.Column('oxidizer_type', sa.String(length=100), nullable=False),
        sa.Column('diluents', sa.String(length=100), nullable=True),
        sa.Column('gravity_level', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('principal_investigators', sa.JSON(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('objectives', sa.Text(), nullable=False),
        sa.Column('apparatus_description', sa.Text(), nullable=True),
        sa.Column('data_completeness_index', sa.Float(), nullable=False),
        sa.Column('nasa_source_url', sa.Text(), nullable=False),
        sa.Column('source_repository', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index('ix_investigations_slug', 'investigations', ['slug'], unique=True)
    op.create_index('ix_investigations_project_acronym', 'investigations', ['project_acronym'], unique=False)
    op.create_index('ix_investigations_facility', 'investigations', ['facility'], unique=False)
    op.create_index('ix_investigations_combustion_regime', 'investigations', ['combustion_regime'], unique=False)
    op.create_index('ix_investigations_fuel_type', 'investigations', ['fuel_type'], unique=False)
    op.create_index('ix_investigations_gravity_level', 'investigations', ['gravity_level'], unique=False)

    # 2. test_runs
    op.create_table(
        'test_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('investigation_id', sa.Uuid(), nullable=False),
        sa.Column('run_identifier', sa.String(length=100), nullable=False),
        sa.Column('run_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fuel_phase', sa.String(length=50), nullable=False),
        sa.Column('chamber_pressure_kpa', sa.Float(), nullable=True),
        sa.Column('ambient_temperature_k', sa.Float(), nullable=True),
        sa.Column('oxygen_percentage', sa.Float(), nullable=True),
        sa.Column('fuel_flow_rate_sccm', sa.Float(), nullable=True),
        sa.Column('droplet_initial_diameter_mm', sa.Float(), nullable=True),
        sa.Column('burn_duration_s', sa.Float(), nullable=True),
        sa.Column('extinction_type', sa.String(length=100), nullable=True),
        sa.Column('burning_rate_constant_k_mm2_s', sa.Float(), nullable=True),
        sa.Column('flame_spread_rate_mm_s', sa.Float(), nullable=True),
        sa.Column('raw_parameters', sa.JSON(), nullable=False),
        sa.Column('si_normalized_parameters', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_runs_investigation_id', 'test_runs', ['investigation_id'], unique=False)
    op.create_index('ix_test_runs_run_identifier', 'test_runs', ['run_identifier'], unique=False)

    # 3. measurements
    op.create_table(
        'measurements',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('test_run_id', sa.Uuid(), nullable=True),
        sa.Column('investigation_id', sa.Uuid(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('time_seconds', sa.Float(), nullable=True),
        sa.Column('value_si', sa.Float(), nullable=True),
        sa.Column('unit_si', sa.String(length=50), nullable=False),
        sa.Column('original_value', sa.String(length=50), nullable=True),
        sa.Column('original_unit', sa.String(length=50), nullable=True),
        sa.Column('conversion_method', sa.String(length=100), nullable=False),
        sa.Column('validation_status', sa.String(length=50), nullable=False),
        sa.Column('sensor_type', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_run_id'], ['test_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_measurements_investigation_id', 'measurements', ['investigation_id'], unique=False)
    op.create_index('ix_measurements_test_run_id', 'measurements', ['test_run_id'], unique=False)
    op.create_index('ix_measurements_metric_name', 'measurements', ['metric_name'], unique=False)

    # 4. provenance_records
    op.create_table(
        'provenance_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('investigation_id', sa.Uuid(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('retrieval_timestamp', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('sha256_checksum', sa.String(length=64), nullable=False),
        sa.Column('http_etag', sa.String(length=100), nullable=True),
        sa.Column('byte_size', sa.BigInteger(), nullable=False),
        sa.Column('parser_module', sa.String(length=100), nullable=False),
        sa.Column('parser_version', sa.String(length=20), nullable=False),
        sa.Column('validation_status', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_provenance_records_investigation_id', 'provenance_records', ['investigation_id'], unique=False)
    op.create_index('ix_provenance_records_sha256_checksum', 'provenance_records', ['sha256_checksum'], unique=False)

    # 5. vector_embeddings
    op.create_table(
        'vector_embeddings',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vector_embeddings_entity_type', 'vector_embeddings', ['entity_type'], unique=False)
    op.create_index('ix_vector_embeddings_entity_id', 'vector_embeddings', ['entity_id'], unique=False)


def downgrade() -> None:
    op.drop_table('vector_embeddings')
    op.drop_table('provenance_records')
    op.drop_table('measurements')
    op.drop_table('test_runs')
    op.drop_table('investigations')
