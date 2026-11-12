from typing import Any

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


class CompareResponse(BaseModel):
    investigation_ids: list[str]
    equivalence_assessment: EquivalenceAssessment
    comparison_grid: dict[str, Any]
