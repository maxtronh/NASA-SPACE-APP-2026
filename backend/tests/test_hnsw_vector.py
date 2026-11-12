"""Tests for Milestone 2: Hierarchical Navigable Small World (HNSW) Indexing on pgvector (Upgrade 11)."""

import importlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, schema
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

migration_0002 = importlib.import_module("backend.alembic.versions.0002_add_hnsw_vector_index")
from backend.app.models.base import Base
from backend.app.models.embedding import VectorEmbedding
from backend.app.services.vector_search_service import (
    VectorSearchService,
    search_vectors,
)


# =====================================================================
# 1. Alembic Migration Structure and DDL Execution Tests
# =====================================================================


def test_migration_revision_identifiers():
    """Verify revision chain connects correctly from 0001 to 0002."""
    assert migration_0002.revision == "0002"
    assert migration_0002.down_revision == "0001"


def test_alembic_script_directory_chain():
    """Verify Alembic recognizes the complete migration chain."""
    cfg = Config("backend/alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    revisions = [rev.revision for rev in script.walk_revisions()]
    assert "0002" in revisions
    assert "0001" in revisions
    rev_0002 = script.get_revision("0002")
    assert rev_0002.down_revision == "0001"


def test_migration_postgresql_upgrade_and_downgrade():
    """Verify that on PostgreSQL dialect, upgrade executes extension, column alter, and HNSW index."""
    mock_bind = MagicMock()
    mock_bind.dialect.name = "postgresql"

    with patch("alembic.op.get_bind", return_value=mock_bind), patch(
        "alembic.op.execute"
    ) as mock_execute:
        migration_0002.upgrade()

        executed_statements = [call[0][0] for call in mock_execute.call_args_list]
        assert any("CREATE EXTENSION IF NOT EXISTS vector;" in stmt for stmt in executed_statements)
        assert any("ALTER TABLE vector_embeddings" in stmt and "vector(384)" in stmt for stmt in executed_statements)
        assert any(
            "CREATE INDEX IF NOT EXISTS ix_vector_embeddings_hnsw_cosine" in stmt
            and "USING hnsw (embedding vector_cosine_ops)" in stmt
            and "WITH (m = 16, ef_construction = 64)" in stmt
            for stmt in executed_statements
        )

    with patch("alembic.op.get_bind", return_value=mock_bind), patch(
        "alembic.op.execute"
    ) as mock_execute:
        migration_0002.downgrade()

        executed_statements = [call[0][0] for call in mock_execute.call_args_list]
        assert any(
            "DROP INDEX IF EXISTS ix_vector_embeddings_hnsw_cosine;" in stmt
            for stmt in executed_statements
        )


def test_migration_sqlite_safe_noop():
    """Verify that on SQLite dialect, upgrade and downgrade perform no operations."""
    mock_bind = MagicMock()
    mock_bind.dialect.name = "sqlite"

    with patch("alembic.op.get_bind", return_value=mock_bind), patch(
        "alembic.op.execute"
    ) as mock_execute:
        migration_0002.upgrade()
        mock_execute.assert_not_called()

    with patch("alembic.op.get_bind", return_value=mock_bind), patch(
        "alembic.op.execute"
    ) as mock_execute:
        migration_0002.downgrade()
        mock_execute.assert_not_called()


# =====================================================================
# 2. SQLAlchemy Model Index Definition and DDL Compilation Tests
# =====================================================================


def test_vector_embedding_table_args_index():
    """Verify VectorEmbedding.__table_args__ contains the HNSW index with proper postgresql kwargs."""
    indexes = [
        arg for arg in VectorEmbedding.__table_args__
        if hasattr(arg, "name") and arg.name == "ix_vector_embeddings_hnsw_cosine"
    ]
    assert len(indexes) == 1, "ix_vector_embeddings_hnsw_cosine index not found in __table_args__"
    idx = indexes[0]

    assert idx.name == "ix_vector_embeddings_hnsw_cosine"
    dialect_kwargs = dict(idx.dialect_kwargs)
    assert dialect_kwargs["postgresql_using"] == "hnsw"
    assert dialect_kwargs["postgresql_with"] == {"m": 16, "ef_construction": 64}
    assert dialect_kwargs["postgresql_ops"] == {"embedding": "vector_cosine_ops"}


def test_vector_embedding_index_ddl_compilation_postgresql():
    """Verify compiling the index with PostgreSQL dialect generates valid HNSW DDL."""
    idx = next(
        idx for idx in VectorEmbedding.__table__.indexes
        if idx.name == "ix_vector_embeddings_hnsw_cosine"
    )
    compiled = schema.CreateIndex(idx).compile(dialect=postgresql.dialect())
    sql_text = str(compiled)

    assert "CREATE INDEX ix_vector_embeddings_hnsw_cosine ON vector_embeddings" in sql_text
    assert "USING hnsw (embedding vector_cosine_ops)" in sql_text
    assert "WITH (m = 16, ef_construction = 64)" in sql_text


def test_vector_embedding_index_ddl_compilation_sqlite():
    """Verify compiling the index with SQLite dialect succeeds as standard index."""
    idx = next(
        idx for idx in VectorEmbedding.__table__.indexes
        if idx.name == "ix_vector_embeddings_hnsw_cosine"
    )
    compiled = schema.CreateIndex(idx).compile(dialect=sqlite.dialect())
    sql_text = str(compiled)

    assert "CREATE INDEX ix_vector_embeddings_hnsw_cosine ON vector_embeddings (embedding)" in sql_text


def test_vector_embedding_cosine_distance_expression():
    """Verify VectorEmbedding.embedding provides cosine_distance expression compiling to <=>."""
    assert hasattr(VectorEmbedding.embedding, "cosine_distance")
    query_vector = [0.1] * 384
    expr = VectorEmbedding.embedding.cosine_distance(query_vector)
    compiled = expr.compile(dialect=postgresql.dialect())
    assert "<=>" in str(compiled)


# =====================================================================
# 3. Vector Search Service Tests (SQLite In-Memory Fallback)
# =====================================================================


@pytest_asyncio.fixture
async def async_sqlite_session():
    """Fixture providing an isolated in-memory SQLite async session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_search_vectors_sqlite_cosine_ordering(async_sqlite_session):
    """Verify SQLite fallback orders candidates accurately by cosine similarity."""
    session = async_sqlite_session

    e1 = VectorEmbedding(
        id=uuid.uuid4(),
        entity_type="investigation",
        entity_id=uuid.uuid4(),
        chunk_index=0,
        chunk_text="Droplet flame extinction in microgravity",
        embedding=[1.0, 0.0, 0.0] + [0.0] * 381,
    )
    e2 = VectorEmbedding(
        id=uuid.uuid4(),
        entity_type="investigation",
        entity_id=uuid.uuid4(),
        chunk_index=0,
        chunk_text="Heptane droplet combustion dynamics",
        embedding=[0.8, 0.6, 0.0] + [0.0] * 381,
    )
    e3 = VectorEmbedding(
        id=uuid.uuid4(),
        entity_type="investigation",
        entity_id=uuid.uuid4(),
        chunk_index=0,
        chunk_text="Solid fuel PMMA flame spread",
        embedding=[0.0, 1.0, 0.0] + [0.0] * 381,
    )
    session.add_all([e1, e2, e3])
    await session.commit()

    query = [1.0, 0.0, 0.0] + [0.0] * 381
    results = await search_vectors(session, query, top_k=3)

    assert len(results) == 3
    assert results[0].id == e1.id  # cos = 1.0
    assert results[1].id == e2.id  # cos = 0.8
    assert results[2].id == e3.id  # cos = 0.0


@pytest.mark.asyncio
async def test_search_vectors_sqlite_top_k_limiting(async_sqlite_session):
    """Verify top_k limits the number of returned records."""
    session = async_sqlite_session

    records = [
        VectorEmbedding(
            id=uuid.uuid4(),
            entity_type="investigation",
            entity_id=uuid.uuid4(),
            chunk_index=i,
            chunk_text=f"Chunk {i}",
            embedding=[float(i), 1.0] + [0.0] * 382,
        )
        for i in range(10)
    ]
    session.add_all(records)
    await session.commit()

    query = [10.0, 1.0] + [0.0] * 382
    results_2 = await search_vectors(session, query, top_k=2)
    assert len(results_2) == 2

    results_5 = await search_vectors(session, query, top_k=5)
    assert len(results_5) == 5


@pytest.mark.asyncio
async def test_search_vectors_sqlite_entity_type_filter(async_sqlite_session):
    """Verify entity_type filtering works in SQLite fallback."""
    session = async_sqlite_session

    e_inv = VectorEmbedding(
        id=uuid.uuid4(),
        entity_type="investigation",
        entity_id=uuid.uuid4(),
        chunk_index=0,
        chunk_text="Investigation Record",
        embedding=[1.0, 0.0] + [0.0] * 382,
    )
    e_pub = VectorEmbedding(
        id=uuid.uuid4(),
        entity_type="publication",
        entity_id=uuid.uuid4(),
        chunk_index=0,
        chunk_text="Publication Record",
        embedding=[1.0, 0.0] + [0.0] * 382,
    )
    session.add_all([e_inv, e_pub])
    await session.commit()

    query = [1.0, 0.0] + [0.0] * 382
    filtered = await search_vectors(session, query, top_k=10, entity_type="publication")
    assert len(filtered) == 1
    assert filtered[0].entity_type == "publication"
    assert filtered[0].id == e_pub.id


@pytest.mark.asyncio
async def test_search_vectors_empty_table(async_sqlite_session):
    """Verify searching an empty table returns an empty list without error."""
    session = async_sqlite_session
    query = [1.0, 0.0] + [0.0] * 382
    results = await search_vectors(session, query, top_k=10)
    assert results == []


@pytest.mark.asyncio
async def test_search_vectors_class_wrapper(async_sqlite_session):
    """Verify VectorSearchService.search_vectors class method operates identically."""
    session = async_sqlite_session
    e = VectorEmbedding(
        id=uuid.uuid4(),
        entity_type="investigation",
        entity_id=uuid.uuid4(),
        chunk_index=0,
        chunk_text="Test",
        embedding=[1.0, 0.0] + [0.0] * 382,
    )
    session.add(e)
    await session.commit()

    query = [1.0, 0.0] + [0.0] * 382
    results = await VectorSearchService.search_vectors(session, query, top_k=5)
    assert len(results) == 1
    assert results[0].id == e.id


# =====================================================================
# 4. Vector Search Service PostgreSQL Path Tests (Mocked)
# =====================================================================


@pytest.mark.asyncio
async def test_search_vectors_postgresql_path():
    """Verify PostgreSQL path sets ef_search and constructs indexed cosine distance query."""
    mock_session = AsyncMock()
    mock_bind = MagicMock()
    mock_bind.dialect.name = "postgresql"
    mock_session.bind = mock_bind
    mock_session.get_bind.return_value = mock_bind

    fake_result = MagicMock()
    fake_result.scalars.return_value.all.return_value = ["mock_record"]
    mock_session.execute.return_value = fake_result

    query = [0.1] * 384
    records = await search_vectors(
        session=mock_session,
        query_vector=query,
        top_k=7,
        ef_search=60,
        entity_type="investigation",
    )
    assert records == ["mock_record"]

    calls = mock_session.execute.call_args_list
    assert len(calls) == 2

    # Check ef_search SET LOCAL call
    set_local_sql = str(calls[0][0][0])
    set_local_params = calls[0][0][1]
    assert "SET LOCAL hnsw.ef_search = :ef" in set_local_sql
    assert set_local_params == {"ef": 60}

    # Check vector query statement
    query_stmt = calls[1][0][0]
    compiled = query_stmt.compile(dialect=postgresql.dialect())
    sql_str = str(compiled)
    assert "<=>" in sql_str
    assert "ORDER BY (vector_embeddings.embedding <=> %(embedding_1)s) ASC" in sql_str
    assert "LIMIT %(param_1)s::INTEGER" in sql_str
    assert "WHERE vector_embeddings.entity_type = %(entity_type_1)s::VARCHAR" in sql_str


@pytest.mark.asyncio
async def test_search_vectors_postgresql_path_without_entity_type():
    """Verify PostgreSQL path constructs query without WHERE clause when entity_type is None."""
    mock_session = AsyncMock()
    mock_bind = MagicMock()
    mock_bind.dialect.name = "postgresql"
    mock_session.bind = None
    mock_session.get_bind = MagicMock(return_value=mock_bind)

    fake_result = MagicMock()
    fake_result.scalars.return_value.all.return_value = ["mock_record_2"]
    mock_session.execute.return_value = fake_result

    query = [0.2] * 384
    records = await search_vectors(
        session=mock_session,
        query_vector=query,
        top_k=10,
        ef_search=40,
        entity_type=None,
    )
    assert records == ["mock_record_2"]

    calls = mock_session.execute.call_args_list
    assert len(calls) == 2
    query_stmt = calls[1][0][0]
    compiled = query_stmt.compile(dialect=postgresql.dialect())
    sql_str = str(compiled)
    assert "WHERE" not in sql_str


def test_vector_embedding_model_attributes_and_columns():
    """Verify VectorEmbedding model preserves all expected column attributes."""
    columns = {c.name: c for c in VectorEmbedding.__table__.columns}
    assert "id" in columns
    assert "entity_type" in columns
    assert "entity_id" in columns
    assert "chunk_index" in columns
    assert "chunk_text" in columns
    assert "embedding" in columns
    assert "metadata_json" in columns

    # Verify primary key and indexes
    assert columns["id"].primary_key is True
    assert columns["entity_type"].index is True
    assert columns["entity_id"].index is True


# =====================================================================
# 5. Error Handling and Boundary Condition Tests
# =====================================================================


@pytest.mark.asyncio
async def test_search_vectors_invalid_ef_search(async_sqlite_session):
    """Verify invalid ef_search values raise ValueError."""
    session = async_sqlite_session
    query = [1.0, 0.0] + [0.0] * 382

    with pytest.raises(ValueError, match="ef_search must be a positive integer"):
        await search_vectors(session, query, ef_search=0)

    with pytest.raises(ValueError, match="ef_search must be a positive integer"):
        await search_vectors(session, query, ef_search=-10)

    with pytest.raises(ValueError, match="ef_search must be a positive integer"):
        await search_vectors(session, query, ef_search="invalid")  # type: ignore


@pytest.mark.asyncio
async def test_search_vectors_invalid_query_vector(async_sqlite_session):
    """Verify empty or None query_vector raises ValueError."""
    session = async_sqlite_session

    with pytest.raises(ValueError, match="query_vector must be a non-empty list of floats"):
        await search_vectors(session, [])

    with pytest.raises(ValueError, match="query_vector must be a non-empty list of floats"):
        await search_vectors(session, None)  # type: ignore


@pytest.mark.asyncio
async def test_search_vectors_top_k_zero_or_negative(async_sqlite_session):
    """Verify top_k <= 0 returns an empty list immediately."""
    session = async_sqlite_session
    query = [1.0, 0.0] + [0.0] * 382

    res_zero = await search_vectors(session, query, top_k=0)
    assert res_zero == []

    res_neg = await search_vectors(session, query, top_k=-5)
    assert res_neg == []


@pytest.mark.asyncio
async def test_search_vectors_zero_norm_vector(async_sqlite_session):
    """Verify query vector with all zeros is handled gracefully without divide-by-zero."""
    session = async_sqlite_session
    e = VectorEmbedding(
        id=uuid.uuid4(),
        entity_type="investigation",
        entity_id=uuid.uuid4(),
        chunk_index=0,
        chunk_text="Test",
        embedding=[1.0, 0.0] + [0.0] * 382,
    )
    session.add(e)
    await session.commit()

    zero_query = [0.0] * 384
    results = await search_vectors(session, zero_query, top_k=5)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_search_vectors_candidate_with_missing_embedding(async_sqlite_session):
    """Verify candidate rows with None, empty, or mismatched embeddings are skipped gracefully."""
    session = async_sqlite_session
    e_valid = VectorEmbedding(
        id=uuid.uuid4(),
        entity_type="investigation",
        entity_id=uuid.uuid4(),
        chunk_index=0,
        chunk_text="Valid",
        embedding=[1.0, 0.0] + [0.0] * 382,
    )
    e_empty = VectorEmbedding(
        id=uuid.uuid4(),
        entity_type="investigation",
        entity_id=uuid.uuid4(),
        chunk_index=1,
        chunk_text="Empty",
        embedding=[],
    )
    e_mismatch = VectorEmbedding(
        id=uuid.uuid4(),
        entity_type="investigation",
        entity_id=uuid.uuid4(),
        chunk_index=2,
        chunk_text="Mismatch",
        embedding=[1.0],
    )
    session.add_all([e_valid, e_empty, e_mismatch])
    await session.commit()

    query = [1.0, 0.0] + [0.0] * 382
    results = await search_vectors(session, query, top_k=5)
    assert len(results) == 1
    assert results[0].id == e_valid.id
