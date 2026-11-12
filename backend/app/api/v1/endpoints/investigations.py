from backend.app.db.session import get_db
from backend.app.schemas.investigation import (
    InvestigationDetailResponse,
    PaginatedInvestigationsResponse,
)
from backend.app.services.investigation_service import InvestigationService
from backend.app.timeseries import (
    DuckDBTimeseriesEngine,
    TimeseriesResponse,
    ensure_flight_telemetry_seeded,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.get("", response_model=PaginatedInvestigationsResponse)
async def list_investigations(
    regime: str | None = Query(default=None, description="Combustion regime filter"),
    fuel: str | None = Query(default=None, description="Fuel type filter"),
    facility: str | None = Query(default=None, description="Facility filter"),
    gravity: str | None = Query(default=None, description="Gravity level filter"),
    search: str | None = Query(default=None, description="Full-text search query"),
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


@router.get("/{id_or_slug}/timeseries", response_model=TimeseriesResponse)
async def get_investigation_timeseries(
    id_or_slug: str,
    metric: str | None = Query(default=None, description="Physical sensor metric channel name"),
    run_id: str | None = Query(default=None, description="Experimental test run identifier"),
    downsample_points: int | None = Query(default=500, description="Target number of downsampled points"),
    start_time: float | None = Query(default=None, description="Start time filter in seconds"),
    end_time: float | None = Query(default=None, description="End time filter in seconds"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves physical measurement time-series telemetry with DuckDB SIMD decimation."""
    detail = await InvestigationService.get_investigation_detail(
        session=db,
        id_or_slug=id_or_slug,
    )
    # Ensure flight telemetry datasets exist
    ensure_flight_telemetry_seeded()

    slug = detail.get("slug") or id_or_slug
    si_measurements = detail.get("provenance", {}).get("si_measurements", {})

    engine = DuckDBTimeseriesEngine()
    try:
        ts_data = engine.query_timeseries(
            investigation_slug=slug,
            run_identifier=run_id,
            metric=metric,
            downsample_points=downsample_points,
            start_time=start_time,
            end_time=end_time,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return {
        "investigation_id": id_or_slug,
        "run_id": run_id or ts_data.get("run_id"),
        "metric": metric or ts_data.get("metric"),
        "measurements": si_measurements,
        "sampling_rate_hz": ts_data.get("sampling_rate_hz", 30.0),
        "total_points": ts_data.get("total_points", 0),
        "downsampled": ts_data.get("downsampled", False),
        "channels": ts_data.get("channels", []),
        "telemetry": ts_data.get("telemetry", []),
        "statistics": ts_data.get("statistics"),
    }
