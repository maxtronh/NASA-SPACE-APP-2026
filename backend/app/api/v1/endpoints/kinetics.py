"""API endpoints for chemical kinetics and cool flame combustion transition modeling."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.kinetics.cool_flame import (
    COOL_FLAME_SUSCEPTIBLE_FUELS,
    CoolFlamePredictionResult,
    CoolFlameTransitionModel,
)
from backend.app.kinetics.pinn_surrogate import (
    PINNDropletSurrogate,
    PINNSurrogatePrediction,
)

router = APIRouter(prefix="/kinetics", tags=["kinetics"])


class CoolFlamePredictRequest(BaseModel):
    fuel: str = Field(default="n-heptane", description="Fuel name (e.g. 'n-heptane', 'n-decane', 'methanol')")
    initial_diameter_mm: float = Field(default=3.0, ge=0.5, le=10.0, description="Initial droplet diameter in mm")
    ambient_o2_percentage: float = Field(default=21.0, ge=8.0, le=100.0, description="Ambient oxygen volume %")
    pressure_kpa: float = Field(default=101.325, ge=20.0, le=500.0, description="Chamber pressure in kPa")
    ambient_temp_k: float = Field(default=298.15, ge=200.0, le=600.0, description="Ambient temperature in K")
    num_trajectory_points: int = Field(default=40, ge=10, le=100, description="Number of trajectory simulation points")


@router.post("/cool-flame/predict", response_model=CoolFlamePredictionResult)
async def predict_cool_flame(payload: CoolFlamePredictRequest):
    """Predicts two-stage droplet combustion and cool flame transition dynamics."""
    try:
        return CoolFlameTransitionModel.predict(
            fuel=payload.fuel,
            initial_diameter_mm=payload.initial_diameter_mm,
            ambient_o2_pct=payload.ambient_o2_percentage,
            chamber_pressure_kpa=payload.pressure_kpa,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get("/cool-flame/fuels")
async def list_cool_flame_fuels():
    """Lists fuels with their molecular properties and cool flame combustion susceptibility."""
    fuels = []
    for key, prop in COOL_FLAME_SUSCEPTIBLE_FUELS.items():
        fuels.append({
            "key": key,
            "name": prop["name"],
            "formula": prop["formula"],
            "critical_d0_mm": prop["critical_d0_mm"],
            "base_k_hot_mm2_s": prop["base_k_hot_mm2_s"],
            "base_k_cool_mm2_s": prop["base_k_cool_mm2_s"],
            "hot_flame_temp_k": prop["hot_flame_temp_k"],
            "cool_flame_temp_k": prop["cool_flame_temp_k"],
            "pathway": prop["pathway"],
            "reference_ntrs": prop["reference_ntrs"],
        })
    return {"fuels": fuels}


class PINNPredictRequest(BaseModel):
    fuel: str = Field(default="n-heptane", description="Fuel name (e.g. 'n-heptane', 'n-decane', 'methanol')")
    initial_diameter_mm: float = Field(default=3.0, ge=0.5, le=10.0, description="Initial droplet diameter in mm")
    ambient_o2_percentage: float = Field(default=21.0, ge=8.0, le=100.0, description="Ambient oxygen volume %")
    pressure_kpa: float = Field(default=101.325, ge=20.0, le=500.0, description="Chamber pressure in kPa")
    num_points: int = Field(default=50, ge=10, le=200, description="Number of trajectory output points")


@router.post("/pinn-surrogate/predict")
async def predict_pinn_surrogate(payload: PINNPredictRequest):
    """Predicts non-linear microgravity droplet burning trajectory using physics-informed surrogate."""
    try:
        res = PINNDropletSurrogate.predict(
            fuel=payload.fuel,
            initial_diameter_mm=payload.initial_diameter_mm,
            ambient_o2_pct=payload.ambient_o2_percentage,
            chamber_pressure_kpa=payload.pressure_kpa,
            num_points=payload.num_points,
        )
        # Return as dict / Pydantic-compatible JSON
        from dataclasses import asdict
        return asdict(res)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
