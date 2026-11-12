"""Unit and integration tests for Antigravity multi-gravity comparison and regime profiling."""

import pytest
from fastapi.testclient import TestClient

from backend.app.core.gravity import (
    GravityLevel,
    calculate_buoyancy_parameter,
    classify_convection_regime,
    classify_flame_geometry,
    classify_soot_behavior,
    generate_buoyancy_warning,
    get_gravity_acceleration,
    get_gravity_regime_category,
    normalize_gravity_level,
)
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_gravity_normalization():
    assert normalize_gravity_level("microgravity (~10^-6 g)") == GravityLevel.MICROGRAVITY.value
    assert normalize_gravity_level("lunar (0.16g)") == GravityLevel.LUNAR.value
    assert normalize_gravity_level("mars gravity") == GravityLevel.MARS.value
    assert normalize_gravity_level("1.0 g terrestrial") == GravityLevel.NORMAL.value
    assert normalize_gravity_level("hypergravity 2g") == GravityLevel.HYPERGRAVITY_2G.value
    assert normalize_gravity_level("5g centrifuge") == GravityLevel.HYPERGRAVITY_5G.value


def test_gravity_convection_and_flame_geometry_classification():
    # Microgravity: suppressed convection, spherical flame, trapped soot
    assert classify_convection_regime("microgravity (~10^-6 g)") == "suppressed"
    assert classify_flame_geometry("microgravity (~10^-6 g)") == "spherical"
    assert classify_soot_behavior("microgravity (~10^-6 g)") == "trapped"

    # Lunar / Mars: moderate convection, teardrop flame, flickering soot
    assert classify_convection_regime("lunar_gravity (0.16 g)") == "moderate"
    assert classify_flame_geometry("lunar_gravity (0.16 g)") == "teardrop"
    assert classify_soot_behavior("lunar_gravity (0.16 g)") == "flickering"

    # Normal / Hypergravity: strong convection, plume flame, rising soot
    assert classify_convection_regime("normal_gravity (1.0 g)") == "strong"
    assert classify_flame_geometry("normal_gravity (1.0 g)") == "plume"
    assert classify_soot_behavior("normal_gravity (1.0 g)") == "rising"


def test_buoyancy_parameter_and_acceleration():
    assert calculate_buoyancy_parameter(GravityLevel.MICROGRAVITY.value) < 0.001
    assert calculate_buoyancy_parameter(GravityLevel.LUNAR.value) == 0.165
    assert calculate_buoyancy_parameter(GravityLevel.NORMAL.value) == 1.0
    assert calculate_buoyancy_parameter(GravityLevel.HYPERGRAVITY_2G.value) == 2.0

    assert get_gravity_acceleration(GravityLevel.MICROGRAVITY.value) < 0.0001
    assert abs(get_gravity_acceleration(GravityLevel.LUNAR.value) - 1.62) < 0.01
    assert abs(get_gravity_acceleration(GravityLevel.NORMAL.value) - 9.80665) < 0.01


def test_generate_buoyancy_warning():
    # Single regime: no warning
    assert generate_buoyancy_warning(["microgravity (~10^-6 g)", "microgravity (~10^-6 g)"]) is None

    # Mixed regimes: explicit scientific non-equivalence warning
    warning = generate_buoyancy_warning(["microgravity (~10^-6 g)", "lunar_gravity (0.16 g)"])
    assert warning is not None
    assert "Scientific Non-Equivalence Warning" in warning
    assert "Grashof-number" in warning


def test_api_list_gravity_regimes(client: TestClient):
    res = client.get("/api/v1/antigravity/regimes")
    assert res.status_code == 200
    data = res.json()
    assert "regimes" in data
    assert len(data["regimes"]) >= 6
    levels = [r["gravity_level"] for r in data["regimes"]]
    assert GravityLevel.MICROGRAVITY.value in levels
    assert GravityLevel.LUNAR.value in levels
    assert GravityLevel.MARS.value in levels
    assert GravityLevel.NORMAL.value in levels


def test_api_antigravity_compare_endpoint(client: TestClient):
    payload = {
        "investigation_ids": ["flex-2-heptane-droplet", "lunar-droplet-burning"],
        "include_equivalence_matrix": True,
    }
    res = client.post("/api/v1/antigravity/compare", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["investigation_ids"] == ["flex-2-heptane-droplet", "lunar-droplet-burning"]
    assert len(data["gravity_regimes_compared"]) >= 2
    assert "gravity_matrix" in data
    assert "flex-2-heptane-droplet" in data["gravity_matrix"]
    assert "lunar-droplet-burning" in data["gravity_matrix"]

    prof_flex = data["gravity_matrix"]["flex-2-heptane-droplet"]
    prof_lunar = data["gravity_matrix"]["lunar-droplet-burning"]
    assert prof_flex["convection_regime"] == "suppressed"
    assert prof_lunar["convection_regime"] == "moderate"

    # Buoyancy warning must be present
    assert data["buoyancy_warning"] is not None
    assert "Scientific Non-Equivalence Warning" in data["buoyancy_warning"]
    assert data["equivalence_assessment"]["equivalent"] is False


def test_api_antigravity_compare_validation_errors(client: TestClient):
    # Fewer than 2 IDs
    res_few = client.post("/api/v1/antigravity/compare", json={"investigation_ids": ["flex-2-heptane-droplet"]})
    assert res_few.status_code == 422

    # Non-existent ID
    res_404 = client.post(
        "/api/v1/antigravity/compare",
        json={"investigation_ids": ["flex-2-heptane-droplet", "non-existent-id-999"]},
    )
    assert res_404.status_code == 404
