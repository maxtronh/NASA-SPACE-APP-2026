from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.investigation import (
    InvestigationDetailResponse,
    PaginatedInvestigationsResponse,
)
from backend.app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.get("", response_model=PaginatedInvestigationsResponse)
async def list_investigations(
    regime: Optional[str] = Query(default=None, description="Combustion regime filter"),
    fuel: Optional[str] = Query(default=None, description="Fuel type filter"),
    facility: Optional[str] = Query(default=None, description="Facility filter"),
    gravity: Optional[str] = Query(default=None, description="Gravity level filter"),
    search: Optional[str] = Query(default=None, description="Full-text search query"),
    limit: int = Query(default=20, ge=1, le=100, description="Items limit per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
):
    """Lists investigations with faceted filtering, text search, and pagination."""
    items, total = await InvestigationService.list_investigations(
        session=db,
        regime=regime,
        fuel=fuel,
        facility=facility,
        gravity=gravity,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.get("/{id_or_slug}", response_model=InvestigationDetailResponse)
async def get_investigation(
    id_or_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full investigation profile, associated test runs, and provenance."""
    detail = await InvestigationService.get_investigation_detail(
        session=db,
        id_or_slug=id_or_slug,
    )
    return detail


@router.get("/{id_or_slug}/runs")
async def get_investigation_runs(
    id_or_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves list of experimental test runs for the specified investigation."""
    detail = await InvestigationService.get_investigation_detail(
        session=db,
        id_or_slug=id_or_slug,
    )
    return detail.get("test_runs", [])


@router.get("/{id_or_slug}/timeseries")
async def get_investigation_timeseries(
    id_or_slug: str,
    metric: Optional[str] = Query(default=None),
    run_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves physical measurement time-series points for droplet burning curves or heat flux."""
    detail = await InvestigationService.get_investigation_detail(
        session=db,
        id_or_slug=id_or_slug,
    )
    si_measurements = detail["provenance"]["si_measurements"]
    return {
        "investigation_id": id_or_slug,
        "run_id": run_id,
        "metric": metric,
        "measurements": si_measurements,
    }
