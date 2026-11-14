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

from backend.app.exploration.solar_physics import (
    PLANETARY_ORBITS,
    THE_25_FACES,
    PlanetaryState,
    HohmannTransferResult,
    FaceTelemetry,
    calculate_planet_position,
    calculate_hohmann_transfer,
    get_all_faces,
    get_face_by_id,
)
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
    Calculate exact Hohmann transfer delta-V, transit duration, and departure phase angles.
    Accurately computes geocentric translunar injection for Earth <-> Moon / Artemis Gateway (~3.1 km/s TLI)
    and heliocentric interplanetary transfers for all other planet pairs.
    """
    try:
        result = calculate_hohmann_transfer(payload.origin_body, payload.target_body)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        raise HTTPException(status_code=500, detail=f"Qwen Copilot inference error: {str(e)}")


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
