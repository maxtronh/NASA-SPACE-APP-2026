import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.investigation import Investigation


class ProvenanceRecord(Base):
    __tablename__ = "provenance_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    retrieval_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    http_etag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    parser_module: Mapped[str] = mapped_column(
        String(100), nullable=False, default="ingestion.parsers.nasa"
    )
    parser_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="1.0.0"
    )
    validation_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="VALIDATED"
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation", back_populates="provenance_records"
    )
