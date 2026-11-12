
from pydantic import BaseModel


class MissingDataMetric(BaseModel):
    present_count: int
    missing_count: int
    completeness_pct: float


class CorpusAnalyticsResponse(BaseModel):
    total_investigations: int
    combustion_regimes: dict[str, int]
    missing_data_matrix: dict[str, MissingDataMetric]
