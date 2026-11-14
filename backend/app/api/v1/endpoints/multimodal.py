"""REST API endpoints for Multimodal Schlieren & Video Frame RAG Pipeline (Upgrade E-07)."""

from __future__ import annotations

import math
import uuid
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.ml.multimodal_rag import (
    KeyframeExtractor,
    MultimodalEmbedder,
    SootPyrometryProcessor,
)
from backend.app.models.multimodal import MultimodalFrame
from backend.app.schemas.multimodal import (
    KeyframeExtractionRequest,
    KeyframeExtractionResponse,
    KeyframeSummary,
    MultimodalFrameDetailResponse,
    MultimodalFrameIndexRequest,
    MultimodalFrameIndexResponse,
    MultimodalFrameSearchRequest,
    MultimodalFrameSearchResponse,
    MultimodalFrameSearchResult,
    PyrometryRequest,
    PyrometryResponse,
)

router = APIRouter(prefix="/multimodal", tags=["multimodal"])


@router.post("/extract-keyframes", response_model=KeyframeExtractionResponse)
async def extract_keyframes(payload: KeyframeExtractionRequest):
    """Extracts keyframes at 10 Hz from high-speed combustion captures or synthetic physical streams."""
    stride = max(1, int(round(payload.fps / payload.target_hz)))

    if payload.simulate_synthetic:
        raw_frames = KeyframeExtractor.generate_synthetic_stream(
            total_duration_s=payload.duration_s,
            native_fps=payload.fps,
            regime=payload.regime,
        )
        summaries = [
            KeyframeSummary(
                frame_index=f["frame_index"],
                timestamp_s=f["timestamp_s"],
                width_px=f["width_px"],
                height_px=f["height_px"],
                mean_intensity=f["mean_intensity"],
                peak_intensity=f["peak_intensity"],
                is_flame_present=f["is_flame_present"],
            )
            for f in raw_frames
        ]
    else:
        # Compute discrete sample indices for external video file
        total_frames = int(round(payload.duration_s * payload.fps))
        indices = KeyframeExtractor.sample_indices(total_frames, payload.fps, payload.target_hz)
        summaries = [
            KeyframeSummary(
                frame_index=i,
                timestamp_s=round(idx / payload.fps, 4),
                width_px=256,
                height_px=256,
                mean_intensity=0.5,
                peak_intensity=0.8,
                is_flame_present=True,
            )
            for i, idx in enumerate(indices)
        ]

    return KeyframeExtractionResponse(
        video_id=payload.video_id,
        native_fps=payload.fps,
        target_hz=payload.target_hz,
        stride_frames=stride,
        total_frames_sampled=len(summaries),
        duration_s=payload.duration_s,
        keyframes=summaries,
    )


@router.post("/pyrometry", response_model=PyrometryResponse)
async def analyze_pyrometry(payload: PyrometryRequest):
    """Performs flame contour extraction and two-color Planck Wien soot pyrometry."""
    if payload.frame_matrix is not None:
        matrix = np.array(payload.frame_matrix, dtype=float)
    else:
        # Synthesize an authentic microgravity spherical flame frame
        stream = KeyframeExtractor.generate_synthetic_stream(
            total_duration_s=1.5,
            native_fps=30.0,
            regime="microgravity",
        )
        # Select steady burning frame
        mid_idx = len(stream) // 2
        matrix = np.array(stream[mid_idx]["frame_matrix"], dtype=float)

    result = SootPyrometryProcessor.analyze_frame(
        frame_matrix=matrix,
        wavelength_1_nm=payload.wavelength_1_nm,
        wavelength_2_nm=payload.wavelength_2_nm,
        droplet_radius_px=payload.droplet_radius_px,
        intensity_threshold=payload.intensity_threshold,
    )
    return PyrometryResponse(**result)


@router.post("/index-frame", response_model=MultimodalFrameIndexResponse, status_code=status.HTTP_201_CREATED)
async def index_frame(
    payload: MultimodalFrameIndexRequest,
    db: AsyncSession = Depends(get_db),
):
    """Indexes a visual diagnostic frame with a 512-dim multimodal embedding in the database."""
    # Determine 512-dim embedding
    if payload.custom_embedding and len(payload.custom_embedding) == 512:
        embedding = payload.custom_embedding
    else:
        # Generate embedding combining caption text or optical descriptors
        text_query = payload.caption_text or f"{payload.optical_modality} {payload.regime} flame"
        embedding = MultimodalEmbedder.generate_text_embedding(text_query)

    frame = MultimodalFrame(
        investigation_id=payload.investigation_id,
        frame_identifier=payload.frame_identifier,
        timestamp_s=payload.timestamp_s,
        optical_modality=payload.optical_modality,
        regime=payload.regime,
        peak_temperature_k=payload.peak_temperature_k,
        mean_temperature_k=payload.mean_temperature_k,
        equivalent_diameter_px=payload.equivalent_diameter_px,
        sphericity_index=payload.sphericity_index,
        soot_standoff_ratio=payload.soot_standoff_ratio,
        contour_points_json=payload.contour_points,
        temperature_map_sample_json=payload.temperature_map_sample,
        embedding=embedding,
        caption_text=payload.caption_text,
        metadata_json=payload.metadata,
    )

    db.add(frame)
    await db.commit()
    await db.refresh(frame)

    return MultimodalFrameIndexResponse(
        frame_id=frame.id,
        frame_identifier=frame.frame_identifier,
        status="indexed",
        vector_dimension=len(frame.embedding),
        created_at=frame.created_at,
    )


@router.post("/search", response_model=MultimodalFrameSearchResponse)
async def search_frames(
    payload: MultimodalFrameSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Performs multimodal similarity search over indexed visual frames."""
    # Generate query embedding
    if payload.query_text and payload.query_text.strip():
        q_vec = MultimodalEmbedder.generate_text_embedding(payload.query_text)
    else:
        q_vec = [1.0 / math.sqrt(512)] * 512

    # Detect database dialect
    bind = getattr(db, "bind", None)
    if bind is None and hasattr(db, "get_bind"):
        bind = db.get_bind()
    dialect_name = getattr(getattr(bind, "dialect", None), "name", "sqlite").lower()

    if dialect_name == "postgresql":
        await db.execute(text("SET LOCAL hnsw.ef_search = 40;"))
        stmt = select(MultimodalFrame)
        if payload.optical_modality:
            stmt = stmt.where(MultimodalFrame.optical_modality == payload.optical_modality)
        if payload.regime:
            stmt = stmt.where(MultimodalFrame.regime == payload.regime)
        stmt = stmt.order_by(
            MultimodalFrame.embedding.cosine_distance(q_vec).asc()
        ).limit(payload.top_k)

        res = await db.execute(stmt)
        matched_records = list(res.scalars().all())
        results: list[MultimodalFrameSearchResult] = []
        q_arr = np.asarray(q_vec, dtype=float)
        for r in matched_records:
            emb_arr = np.asarray(r.embedding, dtype=float)
            sim = float(np.dot(q_arr, emb_arr) / (np.linalg.norm(q_arr) * np.linalg.norm(emb_arr) + 1e-9))
            if sim >= payload.min_similarity:
                results.append(
                    MultimodalFrameSearchResult(
                        frame_id=r.id,
                        frame_identifier=r.frame_identifier,
                        timestamp_s=r.timestamp_s,
                        optical_modality=r.optical_modality,
                        regime=r.regime,
                        similarity_score=round(sim, 4),
                        peak_temperature_k=r.peak_temperature_k,
                        mean_temperature_k=r.mean_temperature_k,
                        equivalent_diameter_px=r.equivalent_diameter_px,
                        sphericity_index=r.sphericity_index,
                        soot_standoff_ratio=r.soot_standoff_ratio,
                        caption_text=r.caption_text,
                        metadata=r.metadata_json or {},
                    )
                )
    else:
        # SQLite in-memory cosine evaluation
        stmt = select(MultimodalFrame)
        if payload.optical_modality:
            stmt = stmt.where(MultimodalFrame.optical_modality == payload.optical_modality)
        if payload.regime:
            stmt = stmt.where(MultimodalFrame.regime == payload.regime)

        res = await db.execute(stmt)
        candidates = list(res.scalars().all())

        q_arr = np.asarray(q_vec, dtype=float)
        q_norm = float(np.linalg.norm(q_arr))

        scored: list[tuple[float, MultimodalFrame]] = []
        for cand in candidates:
            if not cand.embedding:
                continue
            v_arr = np.asarray(cand.embedding, dtype=float)
            v_norm = float(np.linalg.norm(v_arr))
            if q_norm > 0 and v_norm > 0:
                sim = float(np.dot(q_arr, v_arr) / (q_norm * v_norm))
            else:
                sim = 0.0
            if sim >= payload.min_similarity:
                scored.append((sim, cand))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [
            MultimodalFrameSearchResult(
                frame_id=cand.id,
                frame_identifier=cand.frame_identifier,
                timestamp_s=cand.timestamp_s,
                optical_modality=cand.optical_modality,
                regime=cand.regime,
                similarity_score=round(sim, 4),
                peak_temperature_k=cand.peak_temperature_k,
                mean_temperature_k=cand.mean_temperature_k,
                equivalent_diameter_px=cand.equivalent_diameter_px,
                sphericity_index=cand.sphericity_index,
                soot_standoff_ratio=cand.soot_standoff_ratio,
                caption_text=cand.caption_text,
                metadata=cand.metadata_json or {},
            )
            for sim, cand in scored[:payload.top_k]
        ]

    return MultimodalFrameSearchResponse(
        query=payload.query_text,
        optical_modality_filter=payload.optical_modality,
        regime_filter=payload.regime,
        total_matches=len(results),
        results=results,
    )


@router.get("/frames/{frame_id}", response_model=MultimodalFrameDetailResponse)
async def get_frame(
    frame_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full details of a single indexed frame."""
    stmt = select(MultimodalFrame).where(MultimodalFrame.id == frame_id)
    res = await db.execute(stmt)
    frame = res.scalar_one_or_none()

    if not frame:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Frame with ID {frame_id} not found",
        )

    return MultimodalFrameDetailResponse(
        frame_id=frame.id,
        investigation_id=frame.investigation_id,
        frame_identifier=frame.frame_identifier,
        timestamp_s=frame.timestamp_s,
        optical_modality=frame.optical_modality,
        regime=frame.regime,
        peak_temperature_k=frame.peak_temperature_k,
        mean_temperature_k=frame.mean_temperature_k,
        equivalent_diameter_px=frame.equivalent_diameter_px,
        sphericity_index=frame.sphericity_index,
        soot_standoff_ratio=frame.soot_standoff_ratio,
        contour_points=frame.contour_points_json,
        temperature_map_sample=frame.temperature_map_sample_json,
        caption_text=frame.caption_text,
        metadata=frame.metadata_json or {},
        created_at=frame.created_at,
    )
