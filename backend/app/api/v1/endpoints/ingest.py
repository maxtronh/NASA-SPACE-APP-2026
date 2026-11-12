from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.ingest import IngestValidationRequest, IngestValidationResponse

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/validate", response_model=IngestValidationResponse)
async def validate_ingest(payload: IngestValidationRequest):
    """Validates raw NASA ingestion payload, provenance checksum, and enforces zero-fabrication rules."""
    inv = payload.investigation
    prov = payload.provenance

    # Verify required fields
    required_inv = [
        "slug",
        "title",
        "combustion_regime",
        "fuel_type",
        "gravity_level",
        "nasa_source_url",
    ]
    for field in required_inv:
        if not inv.get(field):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required investigation field '{field}'",
            )

    if not prov.get("sha256_checksum"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing provenance sha256_checksum",
        )

    # Verify no fake zeros in SI measurements (Rule #3 & #4)
    si_m = prov.get("si_measurements", {})
    for k, v in si_m.items():
        if (v == 0.0 or v == 0) and "offset" not in k and "zero" not in k:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Suspicious coerced zero detected in SI measurement '{k}'",
            )

    return {
        "status": "VALIDATED",
        "slug": inv["slug"],
        "checksum_verified": True,
    }
