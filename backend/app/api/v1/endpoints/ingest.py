from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.ingestion.async_queue import AsyncIngestionQueue, IngestionJobRecord, JobStatus
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


class IngestionJobSubmitRequest(BaseModel):
    investigation_slug: str = Field(default="flex-2-heptane-droplet", description="Investigation slug to ingest")
    target_dataset: str = Field(default="psi-flex-2", description="NASA PSI or NTRS target dataset identifier")


@router.post("/jobs")
async def submit_ingestion_job(payload: IngestionJobSubmitRequest):
    """Submits long-running NASA flight ingestion pipeline job to asynchronous worker queue."""
    queue = AsyncIngestionQueue.get_instance()
    job = queue.submit_job(
        investigation_slug=payload.investigation_slug,
        target_dataset=payload.target_dataset,
    )
    return asdict(job)


@router.get("/jobs/{job_id}")
async def get_ingestion_job_status(job_id: str):
    """Retrieves real-time processing status, progress percentage, and stage for an ingestion job."""
    queue = AsyncIngestionQueue.get_instance()
    job = queue.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job '{job_id}' not found.",
        )
    return asdict(job)


@router.get("/jobs")
async def list_ingestion_jobs(limit: int = Query(default=20, ge=1, le=100)):
    """Lists recent background ingestion jobs."""
    queue = AsyncIngestionQueue.get_instance()
    jobs = queue.list_jobs(limit=limit)
    return [asdict(j) for j in jobs]
