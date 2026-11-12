"""Safety API endpoints for NASA-STD-6001B spacecraft materials flammability evaluation."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.safety.evaluator import FlammabilityEvaluator
from backend.app.safety.standards import CABIN_ATMOSPHERES, SPACECRAFT_MATERIALS

router = APIRouter(prefix="/safety", tags=["safety"])


class MaterialEvaluationRequest(BaseModel):
    material: str = Field(..., description="Material identifier or name (e.g. 'pmma', 'nomex', 'delrin', 'polycarbonate')")
    oxygen_percentage: float = Field(default=21.0, ge=1.0, le=100.0, description="Ambient oxygen volume %")
    pressure_kpa: float = Field(default=101.325, ge=10.0, le=250.0, description="Chamber/cabin total pressure in kPa")
    thickness_mm: float = Field(default=2.0, ge=0.1, le=50.0, description="Sample thickness in mm")
    gravity_level: str = Field(default="microgravity (~10^-6 g)", description="Gravitational environment")
    ventilation_velocity_cm_s: float = Field(default=3.0, ge=0.0, le=100.0, description="Cabin ventilation velocity in cm/s")


class MaterialEvaluationResponse(BaseModel):
    material_name: str
    chemical_formula: str
    test_conditions: dict[str, Any]
    limiting_oxygen_index: float
    oxygen_margin_pct: float
    test_1_upward_propagation: dict[str, Any]
    test_7_heat_release: dict[str, Any]
    overall_compliance: str
    safety_recommendation: str


@router.post("/evaluate", response_model=MaterialEvaluationResponse)
async def evaluate_material_safety(payload: MaterialEvaluationRequest):
    """Evaluates material sample compliance against NASA-STD-6001B Test 1 and Test 7 criteria."""
    try:
        return FlammabilityEvaluator.evaluate(
            material_key=payload.material,
            oxygen_percentage=payload.oxygen_percentage,
            pressure_kpa=payload.pressure_kpa,
            thickness_mm=payload.thickness_mm,
            gravity_level=payload.gravity_level,
            ventilation_velocity_cm_s=payload.ventilation_velocity_cm_s,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get("/materials")
async def list_spacecraft_materials():
    """Lists standard aerospace materials with limiting oxygen index (LOI) and flammability parameters."""
    materials = []
    for key, p in SPACECRAFT_MATERIALS.items():
        materials.append({
            "key": key,
            "name": p.name,
            "chemical_formula": p.chemical_formula,
            "limiting_oxygen_index": p.limiting_oxygen_index,
            "heat_of_combustion_mj_kg": p.heat_of_combustion_mj_kg,
            "char_forming": p.char_forming,
            "dripping_propensity": p.dripping_propensity,
            "typical_uses": p.typical_uses,
        })
    return {"materials": materials}


@router.get("/cabin-environments")
@router.get("/atmospheres")
async def list_cabin_atmospheres():
    """Returns NASA standard spacecraft cabin atmospheres (ISS, Artemis Gateway, Lunar Habitat, EVA)."""
    atmospheres = []
    for key, a in CABIN_ATMOSPHERES.items():
        atmospheres.append({
            "code": a.code,
            "name": a.name,
            "oxygen_percentage": a.oxygen_percentage,
            "pressure_kpa": a.pressure_kpa,
            "description": a.description,
        })
    return {"cabin_atmospheres": atmospheres, "atmospheres": atmospheres}
