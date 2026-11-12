import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.investigation import Investigation
    from backend.app.models.test_run import TestRun


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    test_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_runs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # STRICT NULL PRESERVATION (Non-Zero Rule): missing values are NULL, NEVER coerced to 0.0
    value_si: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit_si: Mapped[str] = mapped_column(String(50), nullable=False)
    original_value: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    original_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    conversion_method: Mapped[str] = mapped_column(
        String(100), nullable=False, default="deterministic_si_table_v1"
    )
    validation_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="VALIDATED"
    )
    sensor_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation", back_populates="measurements"
    )
    test_run: Mapped[Optional["TestRun"]] = relationship(
        "TestRun", back_populates="measurements"
    )
