from fastapi.testclient import TestClient


def test_list_investigations_default_pagination(client: TestClient):
    """Verifies default listing of investigations returns paginated results."""
    response = client.get("/api/v1/investigations")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 4
    assert len(data["items"]) >= 4

    first = data["items"][0]
    for field in ["slug", "title", "combustion_regime", "fuel_type", "gravity_level", "nasa_source_url"]:
        assert field in first


def test_filter_by_combustion_regime(client: TestClient):
    """Verifies filtering by valid combustion regime."""
    regimes = ["droplet_combustion", "laminar_diffusion", "solid_flame_spread"]
    for reg in regimes:
        res = client.get(f"/api/v1/investigations?regime={reg}")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert item["combustion_regime"] == reg


def test_invalid_combustion_regime_returns_422(client: TestClient):
    """Verifies unscientific or invalid combustion regime returns HTTP 422."""
    res = client.get("/api/v1/investigations?regime=fictitious_warp_fire")
    assert res.status_code == 422
    assert "Invalid combustion regime" in res.json()["detail"]


def test_filter_by_fuel_type(client: TestClient):
    """Verifies filtering by chemical fuel name."""
    res = client.get("/api/v1/investigations?fuel=Methane")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 2  # ACME microgravity and ACME ground
    for item in items:
        assert "methane" in item["fuel_type"].lower()


def test_filter_by_facility(client: TestClient):
    """Verifies filtering by research platform facility."""
    res = client.get("/api/v1/investigations?facility=CIR")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 2
    for item in items:
        assert "cir" in item["facility"].lower() or "combustion integrated rack" in item["facility"].lower()


def test_text_search(client: TestClient):
    """Verifies full-text search against title, summary, acronym, and fuel."""
    res = client.get("/api/v1/investigations?search=PMMA")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 1
    assert "pmma" in items[0]["fuel_type"].lower() or "pmma" in items[0]["summary"].lower()


def test_pagination_boundary_conditions(client: TestClient):
    """Verifies offset and limit validation boundaries."""
    # Negative offset -> 422
    assert client.get("/api/v1/investigations?offset=-1").status_code == 422
    # Zero limit -> 422
    assert client.get("/api/v1/investigations?limit=0").status_code == 422
    # Limit > 100 -> 422
    assert client.get("/api/v1/investigations?limit=105").status_code == 422
    # Offset beyond total -> 200 with empty items
    beyond = client.get("/api/v1/investigations?offset=500")
    assert beyond.status_code == 200
    assert beyond.json()["items"] == []


def test_investigation_detail_profile(client: TestClient):
    """Verifies complete investigation profile retrieval by slug."""
    res = client.get("/api/v1/investigations/flex-2-heptane-droplet")
    assert res.status_code == 200
    data = res.json()
    assert data["investigation"]["slug"] == "flex-2-heptane-droplet"
    assert data["investigation"]["project_acronym"] == "FLEX-2"
    assert "provenance" in data
    assert data["provenance"]["validation_status"] == "VALIDATED"
    assert "si_measurements" in data["provenance"]
    assert data["provenance"]["si_measurements"]["initial_droplet_diameter_m"] == 0.0021


def test_null_preservation_in_detail_profile(client: TestClient):
    """Verifies strict null-preservation: unmeasured values are strictly None/null, never 0.0."""
    res = client.get("/api/v1/investigations/flex-2-heptane-droplet")
    assert res.status_code == 200
    orig = res.json()["provenance"]["original_measurements"]
    assert orig.get("soot_volume_fraction") is None, "Missing soot_volume_fraction must be None, not 0.0"

    bass_res = client.get("/api/v1/investigations/bass-ii-solid-slab")
    assert bass_res.status_code == 200
    bass_orig = bass_res.json()["provenance"]["original_measurements"]
    assert bass_orig.get("radiative_flux") is None, "Missing radiative_flux must be None, not 0.0"
    assert bass_orig.get("initial_droplet_diameter") is None, "Solid fuel initial_droplet_diameter must be None"


def test_nonexistent_slug_returns_404(client: TestClient):
    """Verifies querying non-existent investigation slug returns HTTP 404."""
    res = client.get("/api/v1/investigations/non-existent-mission-slug-999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_investigation_test_runs_endpoint(client: TestClient):
    """Verifies GET /api/v1/investigations/{id}/runs returns test run trials."""
    res = client.get("/api/v1/investigations/flex-2-heptane-droplet/runs")
    assert res.status_code == 200
    runs = res.json()
    assert isinstance(runs, list)
    assert len(runs) >= 1
    assert runs[0]["fuel_phase"] == "liquid_droplet"
    assert runs[0]["burning_rate_constant_k_mm2_s"] == 0.78


def test_investigation_timeseries_endpoint(client: TestClient):
    """Verifies GET /api/v1/investigations/{id}/timeseries returns telemetry points."""
    res = client.get("/api/v1/investigations/flex-2-heptane-droplet/timeseries")
    assert res.status_code == 200
    data = res.json()
    assert data["investigation_id"] == "flex-2-heptane-droplet"
    assert "measurements" in data
