import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, JSONType

if TYPE_CHECKING:
    from backend.app.models.investigation import Investigation
    from backend.app.models.measurement import Measurement


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    run_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fuel_phase: Mapped[str] = mapped_column(String(50), nullable=False)

    # Physical numerical fields strictly NULLABLE (Rule #4: Missing is NULL, not 0.0)
    chamber_pressure_kpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    ambient_temperature_k: Mapped[float | None] = mapped_column(Float, nullable=True)
    oxygen_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuel_flow_rate_sccm: Mapped[float | None] = mapped_column(Float, nullable=True)
    droplet_initial_diameter_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    burn_duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    extinction_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    burning_rate_constant_k_mm2_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    flame_spread_rate_mm_s: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_parameters: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    si_normalized_parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONType, nullable=False, default=dict
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation", back_populates="test_runs"
    )
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement",
        back_populates="test_run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
