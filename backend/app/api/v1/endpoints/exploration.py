"""
Exploration & 25-Faces Solar System Endpoints — Milestone M9
Exposes REST endpoints for:
- GET /api/v1/exploration/faces-25
- GET /api/v1/exploration/planets
- POST /api/v1/exploration/trajectory/calculate
- POST /api/v1/exploration/copilot/chat
- GET /api/v1/exploration/model/metadata
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.core.logging import logger

from backend.app.exploration.solar_physics import (
    PLANETARY_ORBITS,
    THE_25_FACES,
    PlanetaryState,
    HohmannTransferResult,
    CombustionHazardResult,
    FaceTelemetry,
    calculate_planet_position,
    calculate_hohmann_transfer,
    get_all_faces,
    get_face_by_id,
)
from backend.app.kinetics.rekindle_warning import RekindleWarningEngine
from backend.app.safety.eafhi import EAFHIEngine
from backend.app.exploration.qwen_engine import (
    QwenChatRequest,
    QwenChatResponse,
    QwenModelMetadata,
    qwen_copilot_engine,
)

router = APIRouter(prefix="/exploration", tags=["exploration"])


class TrajectoryCalculateRequest(BaseModel):
    origin_body: str = Field(default="Earth", description="Departure body (e.g. Earth, Lunar Gateway, Mars)")
    target_body: str = Field(default="Mars", description="Destination body (e.g. Mars, Moon, Jupiter, Venus)")
    fuel: Optional[str] = Field(default="n-heptane", description="Fuel for microgravity combustion hazard evaluation")
    fuel_temperature_k: Optional[float] = Field(default=720.0, description="Fuel droplet/mixture temperature in Kelvin")
    cabin_oxygen_pct: Optional[float] = Field(default=21.0, description="Spacecraft cabin ambient oxygen percentage")
    cabin_pressure_kpa: Optional[float] = Field(default=101.325, description="Spacecraft cabin ambient pressure in kPa")
    ventilation_velocity_m_s: Optional[float] = Field(default=0.05, description="Cabin ventilation velocity in m/s")
    characteristic_length_m: Optional[float] = Field(default=0.003, description="Characteristic droplet or scale dimension in meters")


class FacesResponse(BaseModel):
    total_faces: int
    faces: List[FaceTelemetry]
    status: str = "ONLINE"


class PlanetsResponse(BaseModel):
    epoch_seconds: float
    total_bodies: int
    planets: List[PlanetaryState]


@router.get("/faces-25", response_model=FacesResponse)
async def get_25_faces() -> FacesResponse:
    """
    Retrieve real-time telemetry matrix across all 25 scientific faces of solar system simulation.
    """
    faces = get_all_faces()
    return FacesResponse(
        total_faces=len(faces),
        faces=faces,
        status="ONLINE",
    )


@router.get("/faces-25/{face_id}", response_model=FaceTelemetry)
async def get_face_detail(face_id: int) -> FaceTelemetry:
    """
    Retrieve single face telemetry details by ID (1..25).
    """
    face = get_face_by_id(face_id)
    if not face:
        raise HTTPException(status_code=404, detail=f"Face ID {face_id} not found in 25 faces matrix.")
    return face


@router.get("/planets", response_model=PlanetsResponse)
async def get_planetary_ephemeris(
    epoch_seconds: float = Query(0.0, description="Epoch offset in seconds from J2000.0")
) -> PlanetsResponse:
    """
    Compute Keplerian ephemeris state vectors and 3D coordinates for all major solar system bodies.
    """
    planets: List[PlanetaryState] = []
    for orbit in PLANETARY_ORBITS.values():
        state = calculate_planet_position(orbit, epoch_seconds=epoch_seconds)
        planets.append(state)

    return PlanetsResponse(
        epoch_seconds=epoch_seconds,
        total_bodies=len(planets),
        planets=planets,
    )


@router.post("/trajectory/calculate", response_model=HohmannTransferResult)
async def calculate_trajectory(payload: TrajectoryCalculateRequest) -> HohmannTransferResult:
    """
    Calculate exact Hohmann transfer delta-V, transit duration, and departure phase angles,
    co-simulated with microgravity cool-flame rekindle kinetics and exploration atmosphere fire safety.
    Accurately computes geocentric translunar injection for Earth <-> Moon / Artemis Gateway (~3.1 km/s TLI)
    and heliocentric interplanetary transfers for all other planet pairs.
    """
    try:
        result = calculate_hohmann_transfer(payload.origin_body, payload.target_body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Multi-agent co-simulation: microgravity cool-flame kinetics & EAFHI cabin safety
    try:
        fuel_name = payload.fuel or "n-heptane"
        fuel_temp = payload.fuel_temperature_k if payload.fuel_temperature_k is not None else 720.0
        char_len = payload.characteristic_length_m if payload.characteristic_length_m is not None else 0.003
        u_vent = payload.ventilation_velocity_m_s if payload.ventilation_velocity_m_s is not None else 0.05
        o2_pct = payload.cabin_oxygen_pct if payload.cabin_oxygen_pct is not None else 21.0
        p_kpa = payload.cabin_pressure_kpa if payload.cabin_pressure_kpa is not None else 101.325

        canonical_fuel, fuel_prof = RekindleWarningEngine.resolve_fuel_profile(fuel_name)
        da_cool, tau_res, tau_chem = RekindleWarningEngine.calculate_damkohler_cool(
            characteristic_length_m=char_len,
            ventilation_velocity_m_s=u_vent,
            fuel=canonical_fuel,
            temperature_k=fuel_temp,
        )
        p_rekindle = RekindleWarningEngine.calculate_rekindle_probability(
            damkohler_cool=da_cool,
            fuel_temp_k=fuel_temp,
            flash_point_k=fuel_prof["flash_point_k"],
            da_crit=fuel_prof.get("da_crit", 1.0),
            theta=fuel_prof.get("theta", 0.20),
            supports_ltc=fuel_prof.get("supports_ltc", True),
        )
        risk_class = RekindleWarningEngine.classify_risk(p_rekindle)

        # Microgravity cruise fire safety calculation
        eafhi_res = EAFHIEngine.calculate_eafhi(
            material="pmma",
            pressure_kpa=p_kpa,
            oxygen_percentage=o2_pct,
            gravity_level="microgravity (~10^-6 g)",
            characteristic_length_m=char_len,
            ventilation_velocity_cm_s=u_vent * 100.0,
        )

        flight_notes = {
            "cruise_phase": (
                "Microgravity freefall (~10^-6 g): buoyant convection is suppressed (Gr -> 0). "
                "Cool-flame radical pools (RO2 <-> QOOH) can persist silently if Da_cool > 1.0, "
                "leading to unexpected rekindling above flash point."
            ),
            "burn_phase": (
                f"Transfer burn acceleration (Delta-V1={result.delta_v_departure_km_s:.2f} km/s, "
                f"Delta-V2={result.delta_v_arrival_km_s:.2f} km/s): thrust creates an effective acceleration field, "
                "restoring buoyant convection (Gr > 0), enhancing convective heat removal and reducing Da_cool."
            ),
            "hazard_differential": (
                f"During the {result.transit_duration_days:.1f}-day cruise, fire risk is {risk_class} "
                f"(Da_cool={da_cool:.2f}, P_rekindle={p_rekindle:.1%}, EAFHI={eafhi_res['eafhi_score']:.3f}). "
                f"Cabin MOC is {eafhi_res['moc_percentage']:.1f}% O2 at {p_kpa:.1f} kPa."
            ),
        }

        result.combustion_hazard = CombustionHazardResult(
            fuel=canonical_fuel,
            fuel_temperature_k=fuel_temp,
            cabin_oxygen_pct=o2_pct,
            cabin_pressure_kpa=p_kpa,
            ventilation_velocity_m_s=u_vent,
            characteristic_length_m=char_len,
            damkohler_cool=round(da_cool, 4),
            da_cool=round(da_cool, 4),
            rekindle_probability=round(p_rekindle, 4),
            risk_classification=risk_class,
            eafhi_score=round(eafhi_res["eafhi_score"], 4),
            hypobaric_moc_pct=round(eafhi_res["moc_percentage"], 2),
            hypobaric_moc=round(eafhi_res["moc_percentage"], 2),
            flammability_class=eafhi_res["flammability_class"],
            tau_res_s=round(tau_res, 6),
            tau_chem_s=round(tau_chem, 6) if tau_chem is not None else None,
            flight_phase_notes=flight_notes,
        )
    except Exception as hazard_err:
        logger.warning(f"Combustion hazard co-simulation calculation note: {hazard_err}")

    return result


@router.post("/copilot/chat", response_model=QwenChatResponse)
async def copilot_chat(payload: QwenChatRequest) -> QwenChatResponse:
    """
    Execute scientific reasoning query through the extracted Qwen 2.5 AI copilot engine.
    Supports natural language queries, face selection context, and delta-V trajectory questions.
    """
    try:
        response = qwen_copilot_engine.chat(payload)
        return response
    except Exception as e:
        logger.exception(f"Qwen Copilot inference error: {e}")
        raise HTTPException(status_code=500, detail="Qwen Copilot scientific inference failed to process query")


@router.get("/model/metadata", response_model=QwenModelMetadata)
async def get_model_metadata() -> QwenModelMetadata:
    """
    Retrieve inspection metadata of extracted Qwen 2.5 LoRA model assets from E:/ai_model.
    """
    return qwen_copilot_engine.metadata


@router.get("/model/training-history")
async def get_training_history() -> Dict[str, Any]:
    """
    Retrieve training convergence metrics, loss history, and domain evaluation for the NASA-trained model.
    """
    return qwen_copilot_engine.get_training_history()
