"""Antigravity API endpoints for multi-gravity combustion comparisons and regime profiling."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.gravity import (
    BUOYANCY_PARAMETERS,
    GRAVITY_ACCELERATION_MS2,
    GravityLevel,
    calculate_buoyancy_parameter,
    classify_convection_regime,
    classify_flame_geometry,
    classify_soot_behavior,
    get_gravity_regime_category,
)
from backend.app.db.session import get_db
from backend.app.schemas.compare import (
    AntigravityCompareRequest,
    AntigravityCompareResponse,
)
from backend.app.services.antigravity_service import AntigravityComparisonService

router = APIRouter(prefix="/antigravity", tags=["antigravity"])


@router.post("/compare", response_model=AntigravityCompareResponse)
async def compare_antigravity(
    payload: AntigravityCompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """Compares investigations across multiple gravitational environments (microgravity, lunar, Mars, 1g, hypergravity)."""
    return await AntigravityComparisonService.compare_with_gravity_regimes(
        session=db,
        investigation_ids=payload.investigation_ids,
        gravity_regimes=payload.gravity_regimes,
        include_equivalence_matrix=payload.include_equivalence_matrix,
    )


@router.get("/regimes")
async def list_gravity_regimes():
    """Lists all supported gravitational combustion regimes with buoyancy and physical convection parameters."""
    regimes = []
    for level in GravityLevel:
        val = level.value
        regimes.append({
            "gravity_level": val,
            "category": get_gravity_regime_category(val),
            "acceleration_ms2": GRAVITY_ACCELERATION_MS2.get(val, 9.80665),
            "buoyancy_parameter": calculate_buoyancy_parameter(val),
            "convection_regime": classify_convection_regime(val),
            "flame_geometry": classify_flame_geometry(val),
            "soot_behavior": classify_soot_behavior(val),
        })
    return {"regimes": regimes}
