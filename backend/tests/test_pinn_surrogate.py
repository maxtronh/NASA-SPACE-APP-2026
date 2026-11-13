"""Unit and integration tests for Physics-Informed Neural Network (PINN) Droplet Combustion Surrogate."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from backend.app.kinetics.pinn_surrogate import PINNDropletSurrogate, PINNSurrogatePrediction
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_pinn_surrogate_n_heptane_cool_flames():
    res = PINNDropletSurrogate.predict(
        fuel="n-heptane",
        initial_diameter_mm=3.0,
        ambient_o2_pct=21.0,
        chamber_pressure_kpa=101.325,
        num_points=40,
    )

    assert isinstance(res, PINNSurrogatePrediction)
    assert res.fuel == "n-heptane"
    assert res.initial_diameter_mm == 3.0
    assert res.cool_flame_observed is True
    assert res.cool_flame_duration_s is not None
    assert res.cool_flame_duration_s > 0.0
    assert res.extinction_diameter_mm > 0.5  # Non-zero extinction diameter
    assert res.total_combustion_duration_s > res.hot_flame_extinction_time_s
    assert len(res.trajectory) == 40


def test_pinn_surrogate_methanol_no_cool_flame():
    res = PINNDropletSurrogate.predict(
        fuel="methanol",
        initial_diameter_mm=2.5,
        ambient_o2_pct=21.0,
        chamber_pressure_kpa=101.325,
        num_points=30,
    )

    assert res.fuel == "methanol"
    assert res.cool_flame_observed is False
    assert res.cool_flame_duration_s is None
    assert res.final_regime == "radiative_extinction"


def test_pinn_surrogate_trajectory_physics_bounds():
    res = PINNDropletSurrogate.predict(
        fuel="n-heptane",
        initial_diameter_mm=4.0,
        ambient_o2_pct=21.0,
        chamber_pressure_kpa=101.325,
        num_points=50,
    )

    for pt in res.trajectory:
        assert pt.time_s >= 0.0
        assert 0.1 <= pt.diameter_mm <= 4.1
        assert 300.0 <= pt.flame_temperature_k <= 2200.0
        assert pt.regime in ("heat_up", "hot_flame", "cool_flame", "extinguished")


def test_api_pinn_surrogate_predict(client):
    payload = {
        "fuel": "n-heptane",
        "initial_diameter_mm": 3.0,
        "ambient_o2_percentage": 21.0,
        "pressure_kpa": 101.325,
        "num_points": 35,
    }
    response = client.post("/api/v1/kinetics/pinn-surrogate/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["fuel"] == "n-heptane"
    assert data["cool_flame_observed"] is True
    assert len(data["trajectory"]) == 35


def test_api_pinn_surrogate_validation_bounds(client):
    payload = {
        "fuel": "n-heptane",
        "initial_diameter_mm": 0.1,  # Below min 0.5mm
    }
    response = client.post("/api/v1/kinetics/pinn-surrogate/predict", json=payload)
    assert response.status_code == 422
