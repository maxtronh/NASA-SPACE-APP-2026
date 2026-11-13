"""
Unit tests for Computer Vision Flame Front and Sphericity Tracking Module.
Verifies geometric extraction, perimeter calculation, sphericity index,
and buoyancy vs microgravity regime classification.
"""

from __future__ import annotations

import numpy as np
import pytest

from backend.app.ml.vision_tracker import FlameVisionTracker


def test_flame_vision_tracker_microgravity_sphere():
    """Spherical microgravity flame should exhibit high sphericity (>= 0.88) and symmetry."""
    frames = FlameVisionTracker.generate_synthetic_flame_frames(
        regime="microgravity",
        num_frames=8,
        grid_size=64,
    )
    result = FlameVisionTracker.track_sequence(
        frames=frames,
        fps=30.0,
        intensity_threshold=0.35,
        droplet_radius_px=5.0,
    )

    assert result.total_frames_analyzed == 8
    assert result.is_microgravity_symmetric is True
    assert result.regime_classification == "microgravity_spherical"
    assert result.mean_sphericity >= 0.88
    assert result.peak_diameter_px > 0.0

    # Verify per-frame metrics
    first_frame = result.frames[0]
    assert first_frame.flame_area_px2 > 0.0
    assert first_frame.perimeter_px > 0.0
    assert first_frame.soot_standoff_ratio is not None
    assert first_frame.soot_standoff_ratio > 1.0


def test_flame_vision_tracker_buoyant_plume():
    """Elongated 1g buoyant plume should exhibit lower sphericity (< 0.88)."""
    frames = FlameVisionTracker.generate_synthetic_flame_frames(
        regime="buoyant",
        num_frames=8,
        grid_size=64,
    )
    result = FlameVisionTracker.track_sequence(
        frames=frames,
        fps=30.0,
        intensity_threshold=0.35,
    )

    assert result.total_frames_analyzed == 8
    assert result.is_microgravity_symmetric is False
    assert result.regime_classification == "buoyant_convective_plume"
    assert result.mean_sphericity < 0.88



def test_flame_vision_tracker_dark_or_empty_frame():
    """Empty / dark image below threshold should return zero area and handle gracefully."""
    empty_frame = np.zeros((64, 64), dtype=float)
    metrics = FlameVisionTracker.analyze_frame(
        image_2d=empty_frame,
        frame_index=0,
        time_s=0.0,
        intensity_threshold=0.35,
    )

    assert metrics.flame_area_px2 == 0.0
    assert metrics.perimeter_px == 0.0
    assert metrics.equivalent_diameter_px == 0.0
    assert metrics.sphericity_index == 0.0


def test_api_vision_simulate_and_track():
    """Verify FastAPI analytics endpoint executes simulation and tracking."""
    from starlette.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    payload = {
        "regime": "microgravity",
        "num_frames": 5,
        "fps": 30.0,
    }
    response = client.post("/api/v1/analytics/vision/simulate-and-track", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_frames_analyzed"] == 5
    assert data["is_microgravity_symmetric"] is True
    assert data["regime_classification"] == "microgravity_spherical"
    assert len(data["frames"]) == 5
