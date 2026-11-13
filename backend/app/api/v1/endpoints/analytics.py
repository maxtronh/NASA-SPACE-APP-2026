from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.ml.vision_tracker import FlameVisionTracker
from backend.app.schemas.analytics import CorpusAnalyticsResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


class VisionSimulationRequest(BaseModel):
    regime: str = Field(default="microgravity", description="Flame regime: 'microgravity' or 'normal_gravity'")
    num_frames: int = Field(default=10, ge=3, le=50, description="Number of video frames to simulate and track")
    fps: float = Field(default=30.0, ge=1.0, le=1000.0, description="Camera frame rate in frames/sec")


@router.post("/vision/simulate-and-track")
async def simulate_and_track_flame_vision(payload: VisionSimulationRequest):
    """Simulates high-speed combustion optical footage and tracks flame edge, sphericity, and regime."""
    frames = FlameVisionTracker.generate_synthetic_flame_frames(
        regime=payload.regime,
        num_frames=payload.num_frames,
    )
    result = FlameVisionTracker.track_sequence(
        frames=frames,
        fps=payload.fps,
        droplet_radius_px=4.0,
    )
    return asdict(result)


@router.get("/corpus", response_model=CorpusAnalyticsResponse)
async def get_corpus_analytics(
    db: AsyncSession = Depends(get_db),
):
    """Corpus completeness overview and missing measurement matrix across scientific channels."""
    data = await AnalyticsService.get_corpus_analytics(session=db)
    return data


@router.get("/overview")
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
):
    """High-level analytics overview for dashboard metrics."""
    data = await AnalyticsService.get_corpus_analytics(session=db)
    return {
        "total_investigations": data["total_investigations"],
        "combustion_regimes": data["combustion_regimes"],
    }


@router.get("/missing-data-analysis")
async def get_missing_data_analysis(
    db: AsyncSession = Depends(get_db),
):
    """Detailed missing data matrix isolating unmeasured physical parameters."""
    data = await AnalyticsService.get_corpus_analytics(session=db)
    return {
        "total_investigations": data["total_investigations"],
        "missing_data_matrix": data["missing_data_matrix"],
    }
