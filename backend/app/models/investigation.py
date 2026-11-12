import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Date, DateTime, Float, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, JSONType

if TYPE_CHECKING:
    from backend.app.models.test_run import TestRun
    from backend.app.models.measurement import Measurement
    from backend.app.models.provenance import ProvenanceRecord


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    short_name: Mapped[str] = mapped_column(String(50), nullable=False)
    project_acronym: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    facility: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    combustion_regime: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fuel_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    oxidizer_type: Mapped[str] = mapped_column(String(100), nullable=False, default="Air")
    diluents: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gravity_level: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    principal_investigators: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONType, nullable=False, default=list
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    objectives: Mapped[str] = mapped_column(Text, nullable=False, default="")
    apparatus_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_completeness_index: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    nasa_source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_repository: Mapped[str] = mapped_column(String(50), nullable=False, default="NASA NTRS")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    test_runs: Mapped[List["TestRun"]] = relationship(
        "TestRun",
        back_populates="investigation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    measurements: Mapped[List["Measurement"]] = relationship(
        "Measurement",
        back_populates="investigation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    provenance_records: Mapped[List["ProvenanceRecord"]] = relationship(
        "ProvenanceRecord",
        back_populates="investigation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
