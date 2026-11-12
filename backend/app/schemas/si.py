from typing import Annotated, Any, Union

from pydantic import BaseModel, Field

from backend.app.schemas.artifacts import ScientificArtifact


class SIQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    filters: dict[str, Any] | None = None


class SICitation(BaseModel):
    investigation_id: str
    title: str
    nasa_source_url: str
    relevance_score: float


class SIExplainability(BaseModel):
    matched_entities: list[str]
    retrieval_method: str = "hybrid_rrf_bm25_vector"
    abstention_reason: str | None = None


class SIQueryResponse(BaseModel):
    query: str
    answer: str
    confidence_score: float
    abstention_flag: bool
    citations: list[SICitation]
    explainability: SIExplainability
    artifacts: list[ScientificArtifact] = Field(default_factory=list)
