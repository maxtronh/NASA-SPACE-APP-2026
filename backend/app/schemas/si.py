from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SIQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    filters: Optional[Dict[str, Any]] = None


class SICitation(BaseModel):
    investigation_id: str
    title: str
    nasa_source_url: str
    relevance_score: float


class SIExplainability(BaseModel):
    matched_entities: List[str]
    retrieval_method: str = "hybrid_rrf_bm25_vector"
    abstention_reason: Optional[str] = None


class SIQueryResponse(BaseModel):
    query: str
    answer: str
    confidence_score: float
    abstention_flag: bool
    citations: List[SICitation]
    explainability: SIExplainability
