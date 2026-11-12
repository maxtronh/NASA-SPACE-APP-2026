"""Vector search service supporting PostgreSQL pgvector HNSW and SQLite in-memory fallback."""

from typing import Optional

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.embedding import VectorEmbedding


async def search_vectors(
    session: AsyncSession,
    query_vector: list[float],
    top_k: int = 20,
    ef_search: int = 40,
    entity_type: Optional[str] = None,
) -> list[VectorEmbedding]:
    """Search for nearest VectorEmbedding records using cosine distance/similarity.

    On PostgreSQL:
        Sets session transaction-scoped `SET LOCAL hnsw.ef_search = :ef` and performs
        an indexed HNSW search using `cosine_distance(query_vector).asc()`.

    On SQLite:
        Scans candidate records (filtered by entity_type if provided) and calculates
        in-memory cosine similarity via NumPy, returning candidates sorted descending.
    """
    if ef_search is None or not isinstance(ef_search, int) or ef_search <= 0:
        raise ValueError(f"ef_search must be a positive integer, got {ef_search}")

    if query_vector is None or len(query_vector) == 0:
        raise ValueError("query_vector must be a non-empty list of floats")

    if top_k <= 0:
        return []

    # Detect dialect
    bind = getattr(session, "bind", None)
    if bind is None and hasattr(session, "get_bind"):
        bind = session.get_bind()
    dialect_name = getattr(getattr(bind, "dialect", None), "name", "sqlite").lower()

    if dialect_name == "postgresql":
        await session.execute(text("SET LOCAL hnsw.ef_search = :ef;"), {"ef": ef_search})

        stmt = select(VectorEmbedding)
        if entity_type is not None:
            stmt = stmt.where(VectorEmbedding.entity_type == entity_type)
        stmt = stmt.order_by(
            VectorEmbedding.embedding.cosine_distance(query_vector).asc()
        ).limit(top_k)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    # SQLite fallback
    stmt = select(VectorEmbedding)
    if entity_type is not None:
        stmt = stmt.where(VectorEmbedding.entity_type == entity_type)

    result = await session.execute(stmt)
    candidates = list(result.scalars().all())
    if not candidates:
        return []

    q = np.asarray(query_vector, dtype=np.float32)
    q_norm = float(np.linalg.norm(q))
    if q_norm == 0.0:
        return candidates[:top_k]

    scored: list[tuple[float, VectorEmbedding]] = []
    for candidate in candidates:
        emb = candidate.embedding
        if emb is None or len(emb) == 0:
            continue
        v = np.asarray(emb, dtype=np.float32)
        if v.shape != q.shape:
            continue
        v_norm = float(np.linalg.norm(v))
        if v_norm == 0.0:
            sim = 0.0
        else:
            sim = float(np.dot(q, v) / (q_norm * v_norm))
        scored.append((sim, candidate))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in scored[:top_k]]


class VectorSearchService:
    """Service class for vector similarity search."""

    @staticmethod
    async def search_vectors(
        session: AsyncSession,
        query_vector: list[float],
        top_k: int = 20,
        ef_search: int = 40,
        entity_type: Optional[str] = None,
    ) -> list[VectorEmbedding]:
        return await search_vectors(
            session=session,
            query_vector=query_vector,
            top_k=top_k,
            ef_search=ef_search,
            entity_type=entity_type,
        )
