"""Tier 1 Opaque Contract Tests for Antigravity Endpoints."""

import pytest
from starlette.testclient import TestClient


def test_tier1_antigravity_regimes_endpoint(api_client: TestClient):
    """Verifies GET /api/v1/antigravity/regimes returns supported gravitational environments."""
    res = api_client.get("/api/v1/antigravity/regimes")
    assert res.status_code == 200
    data = res.json()
    assert "regimes" in data
    assert len(data["regimes"]) >= 4

    regimes_by_level = {r["gravity_level"]: r for r in data["regimes"]}
    assert "microgravity (~10^-6 g)" in regimes_by_level
    micro = regimes_by_level["microgravity (~10^-6 g)"]
    assert micro["convection_regime"] == "suppressed"
    assert micro["flame_geometry"] == "spherical"
    assert micro["soot_behavior"] == "trapped"


def test_tier1_antigravity_compare_contract(api_client: TestClient):
    """Verifies POST /api/v1/antigravity/compare executes and returns full schema contract."""
    payload = {
        "investigation_ids": ["flex-2-heptane-droplet", "acme-cld-ground-1g"],
        "include_equivalence_matrix": True,
    }
    res = api_client.post("/api/v1/antigravity/compare", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "investigation_ids" in data
    assert "gravity_regimes_compared" in data
    assert "equivalence_assessment" in data
    assert "gravity_matrix" in data
    assert "comparison_grid" in data

    # Buoyancy warning between microgravity and 1g
    assert data["buoyancy_warning"] is not None
    assert "Scientific Non-Equivalence Warning" in data["buoyancy_warning"]
    assert data["equivalence_assessment"]["equivalent"] is False


def test_tier1_antigravity_compare_validation_422(api_client: TestClient):
    """Verifies POST /api/v1/antigravity/compare rejects requests with fewer than 2 items."""
    res = api_client.post("/api/v1/antigravity/compare", json={"investigation_ids": ["flex-2-heptane-droplet"]})
    assert res.status_code == 422
