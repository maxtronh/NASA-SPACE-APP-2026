"""SQLAlchemy model for Multimodal Video & Schlieren diagnostic frames (Upgrade E-07).

Supports pgvector Vector(512) on PostgreSQL and JSON fallback on SQLite.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, Float, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, JSONType, VectorType


class MultimodalFrame(Base):
    """Stores visual diagnostic frames (Schlieren, chemiluminescence, shadowgraphy, video).

    Indexed with 512-dimensional multimodal vision/text embeddings for RAG retrieval.
    """

    __tablename__ = "multimodal_frames"

    __table_args__ = (
        Index(
            "ix_multimodal_frames_hnsw_cosine",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    investigation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )
    frame_identifier: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    timestamp_s: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    optical_modality: Mapped[str] = mapped_column(
        String(50), nullable=False, default="schlieren", index=True
    )
    regime: Mapped[str] = mapped_column(
        String(50), nullable=False, default="microgravity", index=True
    )

    # Physical flame geometry & pyrometry (Strict non-zero NULL preservation)
    peak_temperature_k: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mean_temperature_k: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equivalent_diameter_px: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sphericity_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    soot_standoff_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Serialized geometric & pyrometric matrices
    contour_points_json: Mapped[Optional[list[Any]]] = mapped_column(JSONType, nullable=True)
    temperature_map_sample_json: Mapped[Optional[list[Any]]] = mapped_column(JSONType, nullable=True)

    # Multimodal CLIP 512-dim vector embedding
    embedding: Mapped[list[float]] = mapped_column(VectorType(dim=512), nullable=False)

    caption_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONType, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
