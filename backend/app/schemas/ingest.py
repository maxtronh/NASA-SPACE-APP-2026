from typing import Any, Dict
from pydantic import BaseModel


class IngestValidationRequest(BaseModel):
    investigation: Dict[str, Any]
    provenance: Dict[str, Any]


class IngestValidationResponse(BaseModel):
    status: str
    slug: str
    checksum_verified: bool
