"""
Pydantic Data Transfer Objects and Schemas for NASA Ingestion Pipeline.
Conforms strictly to docs/PROJECT_ARCHITECTURE.md and PROJECT.md.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class InvestigationRecord(BaseModel):
    """Investigation metadata schema matching PostgreSQL investigations table."""
    id: str | None = None
    slug: str
    title: str
    short_name: str
    project_acronym: str
    facility: str
    combustion_regime: str
    fuel_type: str
    oxidizer_type: str = "Air"
    diluents: str | None = None
    gravity_level: str = "microgravity (~10^-6 g)"
    start_date: str | None = None
    end_date: str | None = None
    principal_investigators: list[dict[str, str]] = Field(default_factory=list)
    summary: str
    objectives: str = ""
    apparatus_description: str | None = None
    data_completeness_index: float = 0.0
    nasa_source_url: str
    source_repository: str = "NASA NTRS"
    created_at: str | None = None
    updated_at: str | None = None


class TestRunRecord(BaseModel):
    """Individual flight experiment trial matching test_runs table."""
    id: str | None = None
    investigation_id: str | None = None
    run_identifier: str
    run_date: str | None = None
    fuel_phase: str
    chamber_pressure_kpa: float | None = None
    ambient_temperature_k: float | None = None
    oxygen_percentage: float | None = None
    fuel_flow_rate_sccm: float | None = None
    droplet_initial_diameter_mm: float | None = None
    burn_duration_s: float | None = None
    extinction_type: str | None = None
    burning_rate_constant_k_mm2_s: float | None = None
    flame_spread_rate_mm_s: float | None = None
    raw_parameters: dict[str, Any] = Field(default_factory=dict)
    si_normalized_parameters: dict[str, Any] = Field(default_factory=dict)


class MeasurementRecord(BaseModel):
    """Discrete physical observation matching measurements table."""
    id: str | None = None
    test_run_id: str | None = None
    investigation_id: str | None = None
    metric_name: str
    time_seconds: float | None = None
    value_si: float | None = None
    unit_si: str
    original_value: str | None = None
    original_unit: str | None = None
    conversion_method: str
    validation_status: str = "VALID"
    sensor_type: str | None = None


class ProvenanceRecord(BaseModel):
    """Cryptographic audit record matching provenance_records table."""
    id: str | None = None
    investigation_id: str | None = None
    source_url: str
    retrieval_timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    sha256_checksum: str
    http_etag: str | None = None
    byte_size: int = 0
    parser_module: str = "backend.app.ingestion"
    parser_version: str = "1.0.0"
    validation_status: str = "VALIDATED"
    original_measurements: dict[str, Any] | None = None
    si_measurements: dict[str, Any] | None = None
    conversion_method: str | None = "deterministic_si_table_v1"


class IngestionPayload(BaseModel):
    """Complete ingestion payload encapsulating an investigation and its provenance."""
    investigation: InvestigationRecord
    provenance: ProvenanceRecord
    test_runs: list[TestRunRecord] = Field(default_factory=list)
    measurements: list[MeasurementRecord] = Field(default_factory=list)

    def to_contract_dict(self) -> dict[str, Any]:
        """
        Formats payload into the exact interface contract specified in PROJECT.md:
        {
            "investigation": {...},
            "provenance": {...}
        }
        with test_runs and measurements included for detailed persistence.
        """
        return {
            "investigation": self.investigation.model_dump(),
            "provenance": self.provenance.model_dump(),
            "test_runs": [tr.model_dump() for tr in self.test_runs],
            "measurements": [m.model_dump() for m in self.measurements],
        }
