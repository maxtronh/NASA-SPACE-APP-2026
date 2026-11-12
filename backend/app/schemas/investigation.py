from typing import Any

from pydantic import BaseModel


class InvestigationSummary(BaseModel):
    slug: str
    title: str
    project_acronym: str
    facility: str
    combustion_regime: str
    fuel_type: str
    gravity_level: str
    summary: str
    nasa_source_url: str
    source_repository: str

    model_config = {"from_attributes": True}


class PaginatedInvestigationsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[InvestigationSummary]


class ProvenanceInfo(BaseModel):
    source_url: str
    retrieval_timestamp: Any
    sha256_checksum: str
    original_measurements: dict[str, Any]
    si_measurements: dict[str, Any]
    conversion_method: str = "deterministic_si_table_v1"
    validation_status: str = "VALIDATED"


class InvestigationDetailResponse(BaseModel):
    investigation: dict[str, Any]
    provenance: ProvenanceInfo
    test_runs: list[dict[str, Any]] | None = None

    model_config = {"from_attributes": True}
