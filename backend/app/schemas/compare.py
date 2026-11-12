from typing import Any, Dict, List
from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    investigation_ids: List[str] = Field(
        ...,
        min_length=2,
        description="List of at least 2 investigation UUIDs or slugs to compare"
    )


class EquivalenceAssessment(BaseModel):
    equivalent: bool
    reasons: List[str]


class CompareResponse(BaseModel):
    investigation_ids: List[str]
    equivalence_assessment: EquivalenceAssessment
    comparison_grid: Dict[str, Any]
