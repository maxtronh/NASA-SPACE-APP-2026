"""
Pydantic Data Transfer Objects and Schemas for NASA Ingestion Pipeline.
Conforms strictly to docs/PROJECT_ARCHITECTURE.md and PROJECT.md.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InvestigationRecord(BaseModel):
    """Investigation metadata schema matching PostgreSQL investigations table."""
    id: Optional[str] = None
    slug: str
    title: str
    short_name: str
    project_acronym: str
    facility: str
    combustion_regime: str
    fuel_type: str
    oxidizer_type: str = "Air"
    diluents: Optional[str] = None
    gravity_level: str = "microgravity (~10^-6 g)"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    principal_investigators: List[Dict[str, str]] = Field(default_factory=list)
    summary: str
    objectives: str = ""
    apparatus_description: Optional[str] = None
    data_completeness_index: float = 0.0
    nasa_source_url: str
    source_repository: str = "NASA NTRS"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TestRunRecord(BaseModel):
    """Individual flight experiment trial matching test_runs table."""
    id: Optional[str] = None
    investigation_id: Optional[str] = None
    run_identifier: str
    run_date: Optional[str] = None
    fuel_phase: str
    chamber_pressure_kpa: Optional[float] = None
    ambient_temperature_k: Optional[float] = None
    oxygen_percentage: Optional[float] = None
    fuel_flow_rate_sccm: Optional[float] = None
    droplet_initial_diameter_mm: Optional[float] = None
    burn_duration_s: Optional[float] = None
    extinction_type: Optional[str] = None
    burning_rate_constant_k_mm2_s: Optional[float] = None
    flame_spread_rate_mm_s: Optional[float] = None
    raw_parameters: Dict[str, Any] = Field(default_factory=dict)
    si_normalized_parameters: Dict[str, Any] = Field(default_factory=dict)


class MeasurementRecord(BaseModel):
    """Discrete physical observation matching measurements table."""
    id: Optional[str] = None
    test_run_id: Optional[str] = None
    investigation_id: Optional[str] = None
    metric_name: str
    time_seconds: Optional[float] = None
    value_si: Optional[float] = None
    unit_si: str
    original_value: Optional[str] = None
    original_unit: Optional[str] = None
    conversion_method: str
    validation_status: str = "VALID"
    sensor_type: Optional[str] = None


class ProvenanceRecord(BaseModel):
    """Cryptographic audit record matching provenance_records table."""
    id: Optional[str] = None
    investigation_id: Optional[str] = None
    source_url: str
    retrieval_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sha256_checksum: str
    http_etag: Optional[str] = None
    byte_size: int = 0
    parser_module: str = "backend.app.ingestion"
    parser_version: str = "1.0.0"
    validation_status: str = "VALIDATED"
    original_measurements: Optional[Dict[str, Any]] = None
    si_measurements: Optional[Dict[str, Any]] = None
    conversion_method: Optional[str] = "deterministic_si_table_v1"


class IngestionPayload(BaseModel):
    """Complete ingestion payload encapsulating an investigation and its provenance."""
    investigation: InvestigationRecord
    provenance: ProvenanceRecord
    test_runs: List[TestRunRecord] = Field(default_factory=list)
    measurements: List[MeasurementRecord] = Field(default_factory=list)

    def to_contract_dict(self) -> Dict[str, Any]:
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
