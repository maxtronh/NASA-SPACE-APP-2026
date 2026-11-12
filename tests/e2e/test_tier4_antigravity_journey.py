"""Tier 4 End-to-End User Journey for Antigravity Multi-Gravity Comparison Workflow."""

import pytest
from starlette.testclient import TestClient


def test_tier4_antigravity_user_journey(api_client: TestClient):
    """Executes full scientific user journey:
    1. Researcher queries supported gravity environments.
    2. Discovers droplet combustion experiments across microgravity and lunar gravity.
    3. Runs Antigravity multi-gravity comparison to assess convective transport shifts.
    4. Evaluates buoyancy warning and dimensional parameter matrix.
    5. Verifies strict NULL preservation in sparse sensor channels.
    """
    # Step 1: Query regimes
    regimes_res = api_client.get("/api/v1/antigravity/regimes")
    assert regimes_res.status_code == 200
    regimes = regimes_res.json()["regimes"]
    assert any("lunar" in r["gravity_level"].lower() for r in regimes)
    assert any("micro" in r["gravity_level"].lower() for r in regimes)

    # Step 2: Discover investigations
    inv_res = api_client.get("/api/v1/investigations?limit=20")
    assert inv_res.status_code == 200
    items = inv_res.json()["items"]
    slugs = [item["slug"] for item in items]
    assert "flex-2-heptane-droplet" in slugs

    # Step 3: Run Antigravity compare
    compare_payload = {
        "investigation_ids": ["flex-2-heptane-droplet", "acme-cld-flame"],
        "include_equivalence_matrix": True,
    }
    compare_res = api_client.post("/api/v1/antigravity/compare", json=compare_payload)
    assert compare_res.status_code == 200
    compare_data = compare_res.json()

    # Step 4: Validate matrix profiles
    matrix = compare_data["gravity_matrix"]
    assert "flex-2-heptane-droplet" in matrix
    assert "acme-cld-flame" in matrix

    flex_profile = matrix["flex-2-heptane-droplet"]
    assert flex_profile["convection_regime"] == "suppressed"
    assert flex_profile["flame_geometry"] == "spherical"

    # Step 5: Check non-zero NULL preservation
    grid = compare_data["comparison_grid"]
    flex_measurements = grid["flex-2-heptane-droplet"]["si_measurements"]
    assert "soot_volume_fraction_dimensionless" in flex_measurements
    assert flex_measurements["soot_volume_fraction_dimensionless"] is None
