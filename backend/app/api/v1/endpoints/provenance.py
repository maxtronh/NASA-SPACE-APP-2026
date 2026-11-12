"""Provenance API endpoints for cryptographic Merkle audit verification."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.services.merkle_service import FlightArchiveMerkleRegistry

router = APIRouter(prefix="/provenance", tags=["provenance"])


class ProofStep(BaseModel):
    position: str = Field(..., description="'left' or 'right'")
    hash: str = Field(..., description="Hex encoded sibling hash")


class VerifyProofRequest(BaseModel):
    leaf_hash: str = Field(..., description="Target leaf hash")
    proof: list[ProofStep] = Field(..., description="Audit path steps")
    expected_root: str = Field(..., description="Expected Merkle root hash")


class VerifyProofResponse(BaseModel):
    valid: bool
    leaf_hash: str
    expected_root: str
    detail: str


@router.get("/merkle-root")
async def get_merkle_root():
    """Returns cryptographic Merkle root and audit metadata of authentic flight archives."""
    registry = FlightArchiveMerkleRegistry.get_instance()
    return registry.get_root_info()


@router.get("/proof/{identifier}")
async def get_inclusion_proof(identifier: str):
    """Retrieves cryptographic inclusion proof for a NASA flight investigation record."""
    registry = FlightArchiveMerkleRegistry.get_instance()
    try:
        return registry.get_proof(identifier)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation record '{identifier}' not found in Merkle archive",
        )


@router.post("/verify-proof", response_model=VerifyProofResponse)
async def verify_proof(payload: VerifyProofRequest):
    """Verifies a cryptographic Merkle inclusion proof against a target root."""
    registry = FlightArchiveMerkleRegistry.get_instance()
    steps = [s.model_dump() for s in payload.proof]
    is_valid = registry.verify_proof(
        leaf_hash=payload.leaf_hash,
        proof=steps,
        expected_root=payload.expected_root,
    )
    return {
        "valid": is_valid,
        "leaf_hash": payload.leaf_hash,
        "expected_root": payload.expected_root,
        "detail": (
            "Cryptographic proof successfully verified against Merkle root. Data authenticity guaranteed."
            if is_valid
            else "Cryptographic verification failed: proof does not resolve to target root. Record may be altered."
        ),
    }
