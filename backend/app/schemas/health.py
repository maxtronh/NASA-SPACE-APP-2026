from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    tier: Optional[str] = None
    pgvector_ready: bool
    version: str
