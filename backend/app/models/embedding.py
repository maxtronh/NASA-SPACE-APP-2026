import uuid
from typing import Any, Dict, List
from sqlalchemy import Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, JSONType, VectorType


class VectorEmbedding(Base):
    __tablename__ = "vector_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(VectorType(dim=384), nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
