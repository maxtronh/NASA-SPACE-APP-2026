import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, JSONType

if TYPE_CHECKING:
    from backend.app.models.investigation import Investigation


class LiteratureCitation(Base):
    __tablename__ = "literature_citations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    ntrs_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list[str]] = mapped_column(JSONType, nullable=False, default=list)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    journal_or_book: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bibtex: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="VERIFIED_CROSSREF"
    )
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    investigation: Mapped["Investigation"] = relationship("Investigation")

    def to_dict(self) -> dict[str, Any]:
        """Converts model instance to a dictionary."""
        return {
            "id": str(self.id),
            "investigation_id": str(self.investigation_id),
            "doi": self.doi,
            "ntrs_id": self.ntrs_id,
            "title": self.title,
            "authors": self.authors,
            "publication_year": self.publication_year,
            "journal_or_book": self.journal_or_book,
            "bibtex": self.bibtex,
            "verification_status": self.verification_status,
            "sha256_checksum": self.sha256_checksum,
            "raw_metadata": self.raw_metadata,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
        }
