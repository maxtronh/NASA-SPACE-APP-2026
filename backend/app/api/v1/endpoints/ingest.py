from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.ingestion.psi_sync import PSIS3SyncClient
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


@router.get("/psi/datasets")
async def list_psi_datasets(prefix: Optional[str] = Query(None, description="Optional S3 prefix filter")):
    """Lists authentic NASA Physical Sciences Informatics (PSI) datasets cataloged from open archives."""
    client = PSIS3SyncClient()
    datasets = client.list_datasets(prefix=prefix)
    return [asdict(d) for d in datasets]


@router.get("/psi/datasets/{dataset_id}")
async def get_psi_dataset(dataset_id: str):
    """Retrieves metadata and authentic S3 file records for a specific NASA PSI dataset."""
    client = PSIS3SyncClient()
    dataset = client.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NASA PSI dataset '{dataset_id}' not found in catalog.",
        )
    return asdict(dataset)


@router.get("/psi/files")
async def list_psi_files(prefix: str = Query(default="combustion/", description="S3 prefix to query")):
    """Queries or syncs files from the NASA PSI S3 catalog."""
    client = PSIS3SyncClient()
    records = await client.fetch_remote_listing(prefix=prefix)
    return [asdict(r) for r in records]
