"""Independent automated verification suite for Next-Gen Evolutions (E-07, E-08, E-10).

Covers:
- Upgrade E-07: Multimodal Video & Schlieren Diagnostic Frame RAG Engine.
- Upgrade E-08: Active Learning Bayesian Optimal Experiment Design (OED).
- Upgrade E-10: Exploration Atmosphere Fire Hazard Index (EAFHI).
- API endpoints across /api/v1/multimodal, /api/v1/active-learning, /api/v1/safety/eafhi.
"""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.ml.active_learning import (
    FACILITY_CATALOG,
    HISTORICAL_MICROGRAVITY_PRIORS,
    PARAM_BOUNDS,
    GaussianProcessRegressorARD,
    UCBOptimizer,
)
from backend.app.ml.multimodal_rag import (
    KeyframeExtractor,
    MultimodalEmbedder,
    SootPyrometryProcessor,
)
from backend.app.safety.eafhi import EAFHIEngine, SPACECRAFT_MATERIALS


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# E-10: Exploration Atmosphere Fire Hazard Index (EAFHI) Tests
# ---------------------------------------------------------------------------

def test_eafhi_engine_baseline_artemis_gateway():
    """Verifies PMMA under Artemis Exploration Atmosphere (34% O2, 56.5 kPa, lunar gravity)."""
    res = EAFHIEngine.calculate_eafhi(
        material="pmma",
        pressure_kpa=56.5,
        oxygen_percentage=34.0,
        gravity_level="lunar_gravity (0.16 g)",
        characteristic_length_m=0.05,
        ventilation_velocity_cm_s=3.0,
    )
    assert res["material_key"] == "pmma"
    assert 0.0 <= res["eafhi_score"] <= 1.0
    assert res["risk_category"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert res["gas_density_kg_m3"] > 0.0
    assert res["grashof_number"] >= 0.0
    assert res["limiting_oxygen_index_std"] == 17.5
    # PMMA in 34% O2 should be flagged flammable
    assert res["is_flammable"] is True


def test_eafhi_engine_teflon_fire_resistant():
    """Verifies high-performance fluoropolymer (Teflon) remains low risk in standard conditions."""
    res = EAFHIEngine.calculate_eafhi(
        material="teflon",
        pressure_kpa=101.325,
        oxygen_percentage=20.95,
        gravity_level="normal_gravity (1.0 g)",
    )
    assert res["material_key"] == "teflon"
    assert res["limiting_oxygen_index_std"] >= 90.0
    assert res["is_flammable"] is False
    assert res["eafhi_score"] < 0.30
    assert res["flammability_class"] == "CLASS_1_LOW_RISK"


def test_eafhi_api_endpoints(client):
    """Tests /api/v1/safety/eafhi calculation, sensitivity sweep, and gateway profile."""
    # 1. Calculate endpoint
    calc_res = client.post(
        "/api/v1/safety/eafhi/calculate",
        json={
            "material": "nomex",
            "pressure_kpa": 56.5,
            "oxygen_percentage": 30.0,
            "gravity_level": "microgravity (~10^-6 g)",
        },
    )
    assert calc_res.status_code == 200
    data = calc_res.json()
    assert data["material_key"] == "nomex"
    assert "eafhi_score" in data

    # 2. Sensitivity sweep endpoint
    sens_res = client.post(
        "/api/v1/safety/eafhi/sensitivity",
        json={
            "material": "pmma",
            "parameter_to_sweep": "oxygen_percentage",
            "min_value": 15.0,
            "max_value": 45.0,
            "steps": 7,
        },
    )
    assert sens_res.status_code == 200
    sens_data = sens_res.json()
    assert len(sens_data["sweep_values"]) == 7
    assert len(sens_data["eafhi_scores"]) == 7

    # 3. Gateway profile endpoint
    prof_res = client.get("/api/v1/safety/eafhi/gateway-profile")
    assert prof_res.status_code == 200
    prof_data = prof_res.json()
    assert "Gateway" in prof_data["atmosphere_name"]
    assert len(prof_data["material_evaluations"]) >= 6


# ---------------------------------------------------------------------------
# E-08: Active Learning Bayesian OED Tests
# ---------------------------------------------------------------------------

def test_gp_regressor_ard_fit_predict():
    """Verifies Gaussian Process Regressor with ARD kernel."""
    gp = GaussianProcessRegressorARD(noise_var=1e-4)
    X = np.array([
        [101.3, 21.0, 0.0, 2.0],
        [150.0, 30.0, 5.0, 2.5],
        [200.0, 40.0, 10.0, 3.0],
    ])
    y = np.array([0.45, 0.65, 0.88])
    gp.fit(X, y)

    # Predict at training points (should be close to observed)
    mu, sigma = gp.predict(X)
    assert len(mu) == 3
    assert len(sigma) == 3
    assert np.all(sigma >= 0.0)
    assert np.allclose(mu, y, atol=0.15)


def test_ucb_optimizer_proposals():
    """Verifies UCB acquisition function generates ranked proposals respecting bounds."""
    proposals_data = UCBOptimizer.optimize(
        target_metric="burning_rate_mm2_s",
        kappa=2.5,
        num_proposals=4,
        facility="glenn_drop_tower_2_2s",
    )
    assert proposals_data["total_proposals"] == 4
    assert len(proposals_data["proposals"]) == 4

    p1 = proposals_data["proposals"][0]
    assert p1["rank"] == 1
    assert "acquisition_score_ucb" in p1
    assert "estimated_burn_duration_s" in p1
    assert isinstance(p1["estimated_burn_duration_s"], float)
    assert p1["parameters"]["pressure_kpa"] >= PARAM_BOUNDS["pressure_kpa"][0]
    assert p1["parameters"]["pressure_kpa"] <= PARAM_BOUNDS["pressure_kpa"][1]


def test_active_learning_api_endpoints(client):
    """Tests /api/v1/active-learning API endpoints."""
    # 1. Bounds endpoint
    bounds_res = client.get("/api/v1/active-learning/parameter-bounds")
    assert bounds_res.status_code == 200
    b_data = bounds_res.json()
    assert "pressure_kpa" in b_data["bounds"]
    assert len(b_data["facilities"]) >= 4

    # 2. Facilities endpoint
    fac_res = client.get("/api/v1/active-learning/facilities")
    assert fac_res.status_code == 200
    assert len(fac_res.json()) >= 4

    # 3. Optimize endpoint
    opt_res = client.post(
        "/api/v1/active-learning/optimize",
        json={
            "target_metric": "burning_rate_mm2_s",
            "kappa": 2.0,
            "num_proposals": 3,
            "facility": "iss_cir",
        },
    )
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["total_proposals"] == 3


# ---------------------------------------------------------------------------
# E-07: Multimodal Video & Schlieren RAG Tests
# ---------------------------------------------------------------------------

def test_keyframe_extractor():
    """Verifies 10 Hz keyframe extraction and synthetic microgravity flame dynamics."""
    # Subsampling indices
    indices = KeyframeExtractor.sample_indices(total_frames=90, native_fps=30.0, target_hz=10.0)
    assert len(indices) == 30
    assert indices[0] == 0

    # Synthetic stream generation
    frames = KeyframeExtractor.generate_synthetic_stream(
        total_duration_s=1.0, native_fps=30.0, regime="microgravity"
    )
    assert len(frames) == 10
    assert frames[0]["is_flame_present"] in [True, False]
    assert "frame_matrix" in frames[0]


def test_soot_pyrometry_processor():
    """Verifies two-color Wien ratio soot pyrometry and flame geometry."""
    # Create synthetic flame image (RGB)
    img = np.zeros((64, 64, 3), dtype=float)
    # Draw hot central core (soot radiation in red/green channels)
    y, x = np.ogrid[:64, :64]
    r = np.sqrt((x - 32) ** 2 + (y - 32) ** 2)
    flame_mask = r <= 15.0
    img[flame_mask, 0] = 0.8  # Red
    img[flame_mask, 1] = 0.5  # Green
    img[flame_mask, 2] = 0.1  # Blue

    res = SootPyrometryProcessor.analyze_frame(img, droplet_radius_px=5.0)
    assert res["flame_area_px2"] > 0.0
    assert res["sphericity_index"] is not None
    assert 0.0 <= res["sphericity_index"] <= 1.0
    assert res["peak_temperature_k"] is not None
    assert 800.0 <= res["peak_temperature_k"] <= 2400.0


def test_multimodal_embedder():
    """Verifies 512-dim normalized vector embeddings for text and images."""
    text_vec = MultimodalEmbedder.generate_text_embedding("spherical microgravity flame soot halo")
    assert len(text_vec) == 512
    assert np.isclose(np.linalg.norm(text_vec), 1.0, atol=1e-3)

    img = np.ones((32, 32), dtype=float)
    img_vec = MultimodalEmbedder.generate_image_embedding(img)
    assert len(img_vec) == 512
    assert np.isclose(np.linalg.norm(img_vec), 1.0, atol=1e-3)


def test_multimodal_api_endpoints(client):
    """Tests /api/v1/multimodal keyframe extraction and pyrometry endpoints."""
    # 1. Keyframes
    kf_res = client.post(
        "/api/v1/multimodal/extract-keyframes",
        json={
            "video_id": "test_droplet_run_42",
            "fps": 30.0,
            "target_hz": 10.0,
            "duration_s": 1.0,
            "simulate_synthetic": True,
            "regime": "microgravity",
        },
    )
    assert kf_res.status_code == 200
    kf_data = kf_res.json()
    assert kf_data["total_frames_sampled"] == 10
    assert len(kf_data["keyframes"]) == 10

    # 2. Pyrometry
    pyro_res = client.post(
        "/api/v1/multimodal/pyrometry",
        json={
            "video_id": "test_droplet_run_42",
            "optical_modality": "schlieren",
            "droplet_radius_px": 8.0,
        },
    )
    assert pyro_res.status_code == 200
    pyro_data = pyro_res.json()
    assert pyro_data["flame_area_px2"] > 0.0
    assert pyro_data["peak_temperature_k"] is not None
