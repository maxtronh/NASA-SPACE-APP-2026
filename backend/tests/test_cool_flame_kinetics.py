"""Unit and API tests for microgravity cool flame kinetics transition model."""

import pytest
from fastapi.testclient import TestClient

from backend.app.kinetics.cool_flame import (
    COOL_FLAME_SUSCEPTIBLE_FUELS,
    CoolFlameTransitionModel,
)
from backend.app.main import app


def test_cool_flame_fuel_catalog():
    assert "n-heptane" in COOL_FLAME_SUSCEPTIBLE_FUELS
    assert "n-decane" in COOL_FLAME_SUSCEPTIBLE_FUELS
    assert "n-octane" in COOL_FLAME_SUSCEPTIBLE_FUELS
    heptane = COOL_FLAME_SUSCEPTIBLE_FUELS["n-heptane"]
    assert heptane["critical_d0_mm"] == 1.45
    assert heptane["cool_flame_temp_k"] == 720.0


def test_cool_flame_prediction_large_heptane_droplet():
    # Large 3.0 mm n-heptane droplet in microgravity qualifies for two-stage cool flame
    result = CoolFlameTransitionModel.predict(
        fuel="n-heptane",
        initial_diameter_mm=3.0,
        ambient_o2_pct=21.0,
        chamber_pressure_kpa=101.325,
    )
    assert result.cool_flame_predicted is True
    assert result.hot_burning_rate_mm2_s > 0.5
    assert result.cool_burning_rate_mm2_s > 0.1
    assert result.flame_temperature_cool_k == 720.0
    assert result.cool_burn_duration_s > 0.0
    assert result.hot_flame_extinction_diameter_mm is not None
    assert result.final_extinction_diameter_mm is not None
    assert "Two-stage combustion confirmed" in result.regime_narrative


def test_cool_flame_prediction_subcritical_droplet():
    # Small 1.0 mm droplet (< 1.45 mm threshold) burns directly without cool flame
    result = CoolFlameTransitionModel.predict(
        fuel="n-heptane",
        initial_diameter_mm=1.0,
        ambient_o2_pct=21.0,
    )
    assert result.cool_flame_predicted is False
    assert result.hot_flame_extinction_diameter_mm is None
    assert "Single-stage combustion" in result.regime_narrative


def test_cool_flame_prediction_non_ltc_fuel():
    # Methanol does not support low-temperature peroxy chemistry
    result = CoolFlameTransitionModel.predict(
        fuel="methanol",
        initial_diameter_mm=3.0,
        ambient_o2_pct=21.0,
    )
    assert result.cool_flame_predicted is False
    assert "Single-stage" in result.reaction_pathway or "high-temperature" in result.reaction_pathway


def test_api_cool_flame_fuels_endpoint():
    client = TestClient(app)
    res = client.get("/api/v1/kinetics/cool-flame/fuels")
    assert res.status_code == 200
    data = res.json()
    assert "fuels" in data
    assert len(data["fuels"]) >= 3
    fuel_keys = [f["key"] for f in data["fuels"]]
    assert "n-heptane" in fuel_keys
    assert "n-decane" in fuel_keys


def test_api_cool_flame_predict_endpoint():
    client = TestClient(app)
    payload = {
        "fuel": "n-heptane",
        "initial_diameter_mm": 2.8,
        "ambient_o2_percentage": 21.0,
        "pressure_kpa": 101.325,
    }
    res = client.post("/api/v1/kinetics/cool-flame/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["fuel"] == "n-Heptane (C7H16)"
    assert data["cool_flame_predicted"] is True
    assert data["hot_burning_rate_mm2_s"] > 0.0


def test_api_cool_flame_predict_validation_errors():
    client = TestClient(app)
    # Diameter too small (< 0.5 mm in schema)
    res = client.post("/api/v1/kinetics/cool-flame/predict", json={"initial_diameter_mm": 0.1})
    assert res.status_code == 422
