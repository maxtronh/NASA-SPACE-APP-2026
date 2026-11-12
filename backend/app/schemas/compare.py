from typing import Any, Optional

from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    investigation_ids: list[str] = Field(
        ...,
        min_length=2,
        description="List of at least 2 investigation UUIDs or slugs to compare"
    )


class EquivalenceAssessment(BaseModel):
    equivalent: bool
    reasons: list[str]
    buoyancy_warning: Optional[str] = None


class CompareResponse(BaseModel):
    investigation_ids: list[str]
    equivalence_assessment: EquivalenceAssessment
    comparison_grid: dict[str, Any]


class GravityRegimeProfile(BaseModel):
    gravity_level: str
    category: str
    buoyancy_parameter: float
    convection_regime: str
    flame_geometry: str
    soot_behavior: str


class AntigravityCompareRequest(BaseModel):
    investigation_ids: list[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="List of 2 to 5 investigation IDs or slugs across different gravity levels"
    )
    gravity_regimes: Optional[list[str]] = Field(
        default=None,
        description="Optional explicit gravity regime filters to include in comparison"
    )
    include_equivalence_matrix: bool = Field(
        default=True,
        description="Whether to generate full physical equivalence assessment"
    )


class AntigravityCompareResponse(BaseModel):
    investigation_ids: list[str]
    gravity_regimes_compared: list[str]
    equivalence_assessment: EquivalenceAssessment
    gravity_matrix: dict[str, GravityRegimeProfile]
    comparison_grid: dict[str, Any]
    buoyancy_warning: Optional[str] = None
