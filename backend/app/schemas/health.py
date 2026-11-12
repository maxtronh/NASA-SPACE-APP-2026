
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    tier: str | None = None
    pgvector_ready: bool
    version: str
