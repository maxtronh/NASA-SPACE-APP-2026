import uuid
from typing import Any

from sqlalchemy import Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, JSONType, VectorType

try:
    from pgvector.sqlalchemy import Vector as PgVector
    VectorType.comparator_factory = PgVector.Comparator
except (ImportError, AttributeError):
    PgVector = None


class VectorEmbedding(Base):
    __tablename__ = "vector_embeddings"

    __table_args__ = (
        Index(
            "ix_vector_embeddings_hnsw_cosine",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(VectorType(dim=384), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
