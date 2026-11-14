"""Pydantic schemas for Multimodal Video & Schlieren Diagnostic Frames (Upgrade E-07)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class KeyframeSummary(BaseModel):
    """Summary of an extracted keyframe."""

    frame_index: int = Field(..., description="Zero-based index of keyframe in sampled sequence")
    timestamp_s: float = Field(..., description="Timestamp in seconds from test ignition/start")
    width_px: int = Field(default=256, description="Frame width in pixels")
    height_px: int = Field(default=256, description="Frame height in pixels")
    mean_intensity: float = Field(..., description="Average normalized pixel intensity [0.0, 1.0]")
    peak_intensity: float = Field(..., description="Peak normalized pixel intensity [0.0, 1.0]")
    is_flame_present: bool = Field(..., description="Whether flame emission exceeds detection threshold")


class KeyframeExtractionRequest(BaseModel):
    """Request payload for 10 Hz keyframe extraction."""

    video_id: str = Field(..., min_length=1, max_length=100, description="Video/experiment identifier")
    fps: float = Field(default=30.0, ge=1.0, le=2000.0, description="Native video capture framerate in FPS")
    target_hz: float = Field(default=10.0, ge=0.5, le=100.0, description="Target keyframe subsampling frequency (Hz)")
    duration_s: float = Field(default=3.0, ge=0.1, le=120.0, description="Total video duration in seconds")
    simulate_synthetic: bool = Field(default=True, description="Whether to generate authentic microgravity flame dynamics")
    regime: str = Field(default="microgravity", description="Combustion regime (e.g. 'microgravity', 'terrestrial_1g')")


class KeyframeExtractionResponse(BaseModel):
    """Response containing extracted keyframes."""

    video_id: str
    native_fps: float
    target_hz: float
    stride_frames: int
    total_frames_sampled: int
    duration_s: float
    keyframes: list[KeyframeSummary]


class PyrometryRequest(BaseModel):
    """Request payload for two-color Planck Wien soot pyrometry."""

    frame_matrix: Optional[list[list[float]]] = Field(
        default=None,
        description="2D intensity matrix [H, W] normalized to [0.0, 1.0]. If None, a synthetic microgravity flame is generated."
    )
    wavelength_1_nm: float = Field(default=650.0, ge=400.0, le=1000.0, description="Red channel wavelength (nm)")
    wavelength_2_nm: float = Field(default=530.0, ge=400.0, le=1000.0, description="Green channel wavelength (nm)")
    droplet_radius_px: Optional[float] = Field(
        default=None,
        ge=0.1,
        description="Initial droplet radius in pixels for Soot Stand-off Ratio (SSOR). Strict NULL if missing."
    )
    intensity_threshold: float = Field(default=0.20, ge=0.01, le=0.90, description="Threshold for flame boundary detection")


class PyrometryResponse(BaseModel):
    """Response from two-color soot pyrometry and contour extraction."""

    peak_temperature_k: Optional[float] = Field(
        default=None,
        description="Peak flame soot temperature in Kelvin [800.0, 2400.0]. NULL if no soot flame detected."
    )
    mean_temperature_k: Optional[float] = Field(
        default=None,
        description="Mean soot temperature in Kelvin [800.0, 2400.0]. NULL if no soot flame detected."
    )
    flame_area_px2: float = Field(..., description="Projected flame front area in square pixels")
    perimeter_px: float = Field(..., description="Contour boundary perimeter in pixels")
    equivalent_diameter_px: Optional[float] = Field(
        default=None,
        description="Equivalent circular diameter df = 2 * sqrt(Area / pi). NULL if area is negligible."
    )
    sphericity_index: Optional[float] = Field(
        default=None,
        description="Isoperimetric sphericity index Psi = 4 * pi * Area / Perimeter^2 in [0.0, 1.0]. NULL if no flame."
    )
    soot_standoff_ratio: Optional[float] = Field(
        default=None,
        description="SSOR = (df / 2) / r_droplet. Strict non-zero NULL preservation if droplet radius is omitted."
    )
    centroid_x_px: float = Field(..., description="Flame optical centroid X coordinate")
    centroid_y_px: float = Field(..., description="Flame optical centroid Y coordinate")
    temperature_map_sample: Optional[list[list[float]]] = Field(
        default=None,
        description="Downsampled 2D temperature field sample in Kelvin [H_sub, W_sub]"
    )


class MultimodalFrameIndexRequest(BaseModel):
    """Payload to index an analyzed diagnostic frame into the vector store."""

    investigation_id: Optional[uuid.UUID] = Field(default=None, description="Associated investigation ID")
    frame_identifier: str = Field(..., min_length=1, max_length=100, description="Frame identifier")
    timestamp_s: float = Field(default=0.0, ge=0.0, description="Timestamp in seconds")
    optical_modality: str = Field(default="schlieren", description="Imaging modality ('schlieren', 'chemiluminescence_ch', 'backlit')")
    regime: str = Field(default="microgravity", description="Combustion environment regime")
    peak_temperature_k: Optional[float] = Field(default=None, description="Peak temperature in K (Strict NULL preservation)")
    mean_temperature_k: Optional[float] = Field(default=None, description="Mean temperature in K (Strict NULL preservation)")
    equivalent_diameter_px: Optional[float] = Field(default=None, description="Equivalent diameter (Strict NULL preservation)")
    sphericity_index: Optional[float] = Field(default=None, description="Sphericity index (Strict NULL preservation)")
    soot_standoff_ratio: Optional[float] = Field(default=None, description="SSOR (Strict NULL preservation)")
    caption_text: Optional[str] = Field(default=None, description="Descriptive optical caption")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary trial metadata")
    contour_points: Optional[list[Any]] = Field(default=None, description="Boundary contour vertices")
    temperature_map_sample: Optional[list[list[float]]] = Field(default=None, description="Pyrometry temperature field sample")
    custom_embedding: Optional[list[float]] = Field(default=None, description="Optional precomputed 512-dim vector")


class MultimodalFrameIndexResponse(BaseModel):
    """Response after indexing a frame."""

    frame_id: uuid.UUID
    frame_identifier: str
    status: str = "indexed"
    vector_dimension: int = 512
    created_at: datetime


class MultimodalFrameSearchRequest(BaseModel):
    """Payload for multimodal RAG similarity search."""

    query_text: Optional[str] = Field(default=None, description="Semantic text query (e.g. 'spherical soot shell in microgravity')")
    optical_modality: Optional[str] = Field(default=None, description="Filter by optical modality")
    regime: Optional[str] = Field(default=None, description="Filter by combustion regime")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of nearest neighbors to retrieve")
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum cosine similarity cutoff")


class MultimodalFrameSearchResult(BaseModel):
    """Individual search match from multimodal vector store."""

    frame_id: uuid.UUID
    frame_identifier: str
    timestamp_s: float
    optical_modality: str
    regime: str
    similarity_score: float = Field(..., description="Cosine similarity [0.0, 1.0]")
    peak_temperature_k: Optional[float] = None
    mean_temperature_k: Optional[float] = None
    equivalent_diameter_px: Optional[float] = None
    sphericity_index: Optional[float] = None
    soot_standoff_ratio: Optional[float] = None
    caption_text: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultimodalFrameSearchResponse(BaseModel):
    """Response containing matched diagnostic frames."""

    query: Optional[str] = None
    optical_modality_filter: Optional[str] = None
    regime_filter: Optional[str] = None
    total_matches: int
    results: list[MultimodalFrameSearchResult]


class MultimodalFrameDetailResponse(BaseModel):
    """Full detail of a single indexed frame."""

    frame_id: uuid.UUID
    investigation_id: Optional[uuid.UUID] = None
    frame_identifier: str
    timestamp_s: float
    optical_modality: str
    regime: str
    peak_temperature_k: Optional[float] = None
    mean_temperature_k: Optional[float] = None
    equivalent_diameter_px: Optional[float] = None
    sphericity_index: Optional[float] = None
    soot_standoff_ratio: Optional[float] = None
    contour_points: Optional[list[Any]] = None
    temperature_map_sample: Optional[list[list[float]]] = None
    caption_text: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
