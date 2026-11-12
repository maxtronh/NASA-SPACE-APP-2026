from typing import Any

from pydantic import BaseModel


class IngestValidationRequest(BaseModel):
    investigation: dict[str, Any]
    provenance: dict[str, Any]


class IngestValidationResponse(BaseModel):
    status: str
    slug: str
    checksum_verified: bool
