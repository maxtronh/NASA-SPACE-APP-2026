"""Unit and integration tests for Active Learning Bayesian OED (Upgrade E-08)."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.ml.active_learning import (
    FACILITY_CATALOG,
    HISTORICAL_MICROGRAVITY_PRIORS,
    PARAM_BOUNDS,
    GaussianProcessRegressorARD,
    UCBOptimizer,
)


def test_gp_regressor_normalization():
    # Test normalization and denormalization round-trip
    X_orig = np.array([
        [20.0, 12.0, 0.0, 0.5],     # min bounds
        [300.0, 50.0, 30.0, 6.0],   # max bounds
        [101.3, 21.0, 5.0, 2.0],    # nominal
    ])
    X_norm = GaussianProcessRegressorARD.normalize_x(X_orig)
    assert np.all(X_norm >= 0.0)
    assert np.all(X_norm <= 1.0)
    assert pytest.approx(X_norm[0], abs=1e-5) == [0.0, 0.0, 0.0, 0.0]
    assert pytest.approx(X_norm[1], abs=1e-5) == [1.0, 1.0, 1.0, 1.0]

    X_recovered = GaussianProcessRegressorARD.denormalize_x(X_norm)
    assert np.allclose(X_orig, X_recovered, atol=1e-5)


def test_gp_regressor_fit_and_predict():
    gp = GaussianProcessRegressorARD()
    X = np.array([
        [101.3, 21.0, 0.0, 2.0],
        [101.3, 30.0, 0.0, 2.1],
        [50.0, 30.0, 0.0, 1.8],
        [200.0, 21.0, 0.0, 2.2],
    ])
    y = np.array([0.68, 0.82, 0.65, 0.79])

    gp.fit(X, y)
    means, stds = gp.predict(X)

    # Predictions at training points should closely match observed values
    assert np.allclose(means, y, atol=0.08)
    # Uncertainties at training points should be small
    assert np.all(stds < 0.25)

    # Predict at a far unexplored point -> epistemic uncertainty should be higher
    X_unexplored = np.array([[290.0, 48.0, 28.0, 5.8]])
    _, std_far = gp.predict(X_unexplored)
    assert std_far[0] > np.mean(stds)


def test_ucb_optimizer_facility_envelope_constraints():
    # Test optimization for Glenn 2.2s Drop Tower (max d0 = 2.0 mm, max V = 15 cm/s)
    res = UCBOptimizer.optimize(
        target_metric="burning_rate_mm2_s",
        kappa=2.0,
        num_proposals=5,
        facility="glenn_drop_tower_2_2s",
    )
    assert res["total_proposals"] == 5
    assert len(res["proposals"]) == 5

    for p in res["proposals"]:
        params = p["parameters"]
        assert params["initial_diameter_mm"] <= 2.0
        assert params["ventilation_cm_s"] <= 15.0
        assert params["pressure_kpa"] >= 50.0
        assert params["pressure_kpa"] <= 200.0
        assert p["acquisition_score_ucb"] > 0.0
        assert "rationale" in p
        assert "facility_compatibility" in p


def test_ucb_optimizer_fixed_parameters():
    res = UCBOptimizer.optimize(
        num_proposals=3,
        fixed_parameters={"pressure_kpa": 101.3},
    )
    assert len(res["proposals"]) == 3
    for p in res["proposals"]:
        assert pytest.approx(p["parameters"]["pressure_kpa"], abs=0.1) == 101.3


def test_api_optimize_endpoint(client: TestClient):
    payload = {
        "target_metric": "burning_rate_mm2_s",
        "kappa": 2.5,
        "num_proposals": 4,
        "facility": "iss_cir",
    }
    res = client.post("/api/v1/active-learning/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["target_metric"] == "burning_rate_mm2_s"
    assert data["kappa"] == 2.5
    assert data["facility"] == "iss_cir"
    assert data["total_proposals"] == 4
    assert len(data["proposals"]) == 4
    assert data["model_fit_rmse"] >= 0.0
    assert "pressure_kpa" in data["ard_lengthscales"]


def test_api_optimize_with_custom_priors(client: TestClient):
    payload = {
        "num_proposals": 2,
        "priors": [
            {
                "parameters": {
                    "pressure_kpa": 60.0,
                    "oxygen_pct": 25.0,
                    "ventilation_cm_s": 2.0,
                    "initial_diameter_mm": 1.5,
                },
                "observed_value": 0.72,
            },
            {
                "parameters": {
                    "pressure_kpa": 120.0,
                    "oxygen_pct": 35.0,
                    "ventilation_cm_s": 5.0,
                    "initial_diameter_mm": 2.0,
                },
                "observed_value": 0.88,
            },
        ],
    }
    res = client.post("/api/v1/active-learning/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["prior_trials_count"] == 2
    assert len(data["proposals"]) == 2


def test_api_surrogate_predict_endpoint(client: TestClient):
    payload = {
        "points": [
            {
                "pressure_kpa": 56.5,
                "oxygen_pct": 34.0,
                "ventilation_cm_s": 3.0,
                "initial_diameter_mm": 2.0,
            },
            {
                "pressure_kpa": 101.325,
                "oxygen_pct": 21.0,
                "ventilation_cm_s": 0.0,
                "initial_diameter_mm": 2.0,
            },
        ],
        "kappa": 2.0,
    }
    res = client.post("/api/v1/active-learning/surrogate/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 2
    pred = data["predictions"][0]
    assert "mean" in pred
    assert "std" in pred
    assert "ucb" in pred
    assert "entropy" in pred
    assert pred["ucb"] == pytest.approx(pred["mean"] + 2.0 * pred["std"], abs=1e-3)


def test_api_parameter_bounds_and_facilities(client: TestClient):
    # Parameter bounds
    b_res = client.get("/api/v1/active-learning/parameter-bounds")
    assert b_res.status_code == 200
    b_data = b_res.json()
    assert "bounds" in b_data
    assert "pressure_kpa" in b_data["bounds"]
    assert b_data["bounds"]["pressure_kpa"] == [20.0, 300.0]
    assert "facilities" in b_data
    assert len(b_data["facilities"]) >= 4

    # Facilities
    f_res = client.get("/api/v1/active-learning/facilities")
    assert f_res.status_code == 200
    f_data = f_res.json()
    assert isinstance(f_data, list)
    facility_ids = [f["facility_id"] for f in f_data]
    assert "iss_cir" in facility_ids
    assert "glenn_drop_tower_2_2s" in facility_ids


def test_api_predict_validation_errors(client: TestClient):
    # Out of bounds pressure (< 20 kPa)
    payload_bad = {
        "points": [
            {
                "pressure_kpa": 5.0,
                "oxygen_pct": 21.0,
                "ventilation_cm_s": 0.0,
                "initial_diameter_mm": 2.0,
            }
        ]
    }
    res = client.post("/api/v1/active-learning/surrogate/predict", json=payload_bad)
    assert res.status_code == 422
