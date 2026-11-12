"""
Flame in Freefall — FastAPI Core Application
CORTEXX Scientific Intelligence Platform

Wires SQLAlchemy 2.0 ORM models, dual-tier DB session (PostgreSQL + SQLite fallback),
and Pydantic v2 schemas into live REST endpoints conforming to PROJECT.md contracts.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, status

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.session import get_db, init_db, check_db_health
from backend.app.models.investigation import Investigation
from backend.app.models.measurement import Measurement
from backend.app.models.provenance import ProvenanceRecord
from backend.app.models.test_run import TestRun
from backend.app.schemas import (
    HealthResponse,
    InvestigationSummary,
    PaginatedInvestigationsResponse,
    InvestigationDetailResponse,
    ProvenanceInfo,
    IngestValidationRequest,
    IngestValidationResponse,
    CompareRequest,
    CompareResponse,
    EquivalenceAssessment,
    MissingDataMetric,
    CorpusAnalyticsResponse,
    SIQueryRequest,
    SIQueryResponse,
    SICitation,
    SIExplainability,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and extensions on application startup."""
    logger.info("Starting Flame in Freefall backend (version %s)", settings.VERSION)
    try:
        await init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc)
    yield
    logger.info("Shutting down Flame in Freefall backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@app.get(
    settings.API_V1_PREFIX + "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Service and database health check",
)
async def health() -> HealthResponse:
    """Return service health, database connectivity, tier, and pgvector readiness."""
    health_dict = await check_db_health()
    return HealthResponse(**health_dict)


# ---------------------------------------------------------------------------
# Investigations catalog (list + detail)
# ---------------------------------------------------------------------------


@app.get(
    settings.API_V1_PREFIX + "/investigations",
    response_model=PaginatedInvestigationsResponse,
    tags=["investigations"],
    summary="List investigations with faceted filtering and pagination",
)
async def list_investigations(
    regime: Optional[str] = Query(None, description="Filter by combustion regime"),
    fuel: Optional[str] = Query(None, description="Filter by fuel type"),
    facility: Optional[str] = Query(None, description="Filter by facility"),
    gravity_level: Optional[str] = Query(None, description="Filter by gravity level"),
    search: Optional[str] = Query(None, description="Full-text search on title/summary"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> PaginatedInvestigationsResponse:
    """Paginated, filterable catalog of microgravity combustion investigations."""
    async for session in get_db():
        from sqlalchemy import select, func as sql_func

        stmt = select(Investigation)
        if regime:
            stmt = stmt.where(Investigation.combustion_regime == regime)
        if fuel:
            stmt = stmt.where(Investigation.fuel_type.ilike(f"%{fuel}%"))
        if facility:
            stmt = stmt.where(Investigation.facility.ilike(f"%{facility}%"))
        if gravity_level:
            stmt = stmt.where(Investigation.gravity_level == gravity_level)
        if search:
            stmt = stmt.where(
                Investigation.title.ilike(f"%{search}%")
                | Investigation.summary.ilike(f"%{search}%")
            )

        count_stmt = select(sql_func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar() or 0

        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        investigations = result.scalars().all()

        items = [
            InvestigationSummary(
                slug=inv.slug,
                title=inv.title,
                project_acronym=inv.project_acronym,
                facility=inv.facility,
                combustion_regime=inv.combustion_regime,
                fuel_type=inv.fuel_type,
                gravity_level=inv.gravity_level,
                summary=inv.summary,
                nasa_source_url=inv.nasa_source_url,
                source_repository=inv.source_repository,


@app.get(
    settings.API_V1_PREFIX + "/investigations/{investigation_id}",
    response_model=InvestigationDetailResponse,
    tags=["investigations"],
    summary="Detailed investigation profile with runs, measurements, provenance",
)
async def get_investigation(investigation_id: str) -> InvestigationDetailResponse:
    """Return a single investigation by UUID or slug, with provenance and test runs."""
    async for session in get_db():
        from sqlalchemy import select

        try:
            import uuid as uuid_module

            inv_uuid = uuid_module.UUID(investigation_id)
            stmt = select(Investigation).where(Investigation.id == inv_uuid)
        except (ValueError, AttributeError):
            stmt = select(Investigation).where(Investigation.slug == investigation_id)

        result = await session.execute(stmt)
        investigation = result.scalar_one_or_none()
        if investigation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation not found: {investigation_id}",
            )

        prov_stmt = (
            select(ProvenanceRecord)
            .where(ProvenanceRecord.investigation_id == investigation.id)
            .order_by(ProvenanceRecord.retrieval_timestamp.desc())
            .limit(1)
        )
        prov_result = await session.execute(prov_stmt)
        provenance = prov_result.scalar_one_or_none()

        runs_stmt = select(TestRun).where(TestRun.investigation_id == investigation.id)
        runs_result = await session.execute(runs_stmt)
        test_runs = runs_result.scalars().all

        provenance_info = None
        if provenance is not None:
            provenance_info = ProvenanceInfo(
                source_url=provenance.source_url,
                retrieval_timestamp=provenance.retrieval_timestamp,
                sha256_checksum=provenance.sha256_checksum,
                original_measurements={},
                si_measurements={},
                conversion_method=provenance.conversion_method,
                validation_status=provenance.validation_status,
            )

        return InvestigationDetailResponse(
            investigation={
                "id": str(investigation.id),
                "slug": investigation.slug,
                "title": investigation.title,
                "short_name": investigation.short_name,
                "project_acronym": investigation.project_acronym,
                "facility": investigation.facility,
                "combustion_regime": investigation.combustion_regime,
                "fuel_type": investigation.fuel_type,
                "oxidizer_type": investigation.oxidizer_type,
                "gravity_level": investigation.gravity_level,
                "summary": investigation.summary,
                "objectives": investigation.objectives,
                "nasa_source_url": investigation.nasa_source_url,
                "source_repository": investigation.source_repository,
                "data_completeness_index": investigation.data_completeness_index,
            },
            provenance=provenance_info,
            test_runs=[
                {
                    "run_identifier": tr.run_identifier,
                    "fuel_phase": tr.fuel_phase,
                    "raw_parameters": tr.raw_parameters,
                    "si_normalized_parameters": tr.si_normalized_parameters,
                }
                for tr in test_runs
            ],
        )
            )
            for inv in investigations
        ]

        return PaginatedInvestigationsResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=items,
        )
