from fastapi.testclient import TestClient


def test_corpus_analytics_endpoint(client: TestClient):
    """Verifies GET /api/v1/analytics/corpus returns complete breakdown and missingness matrix."""
    res = client.get("/api/v1/analytics/corpus")
    assert res.status_code == 200
    data = res.json()
    assert "total_investigations" in data
    assert "combustion_regimes" in data
    assert "missing_data_matrix" in data

    assert data["total_investigations"] >= 4
    regimes = data["combustion_regimes"]
    assert "droplet_combustion" in regimes
    assert "laminar_diffusion" in regimes
    assert "solid_flame_spread" in regimes

    matrix = data["missing_data_matrix"]
    assert len(matrix) >= 5
    for stats in matrix.values():
        assert "present_count" in stats
        assert "missing_count" in stats
        assert "completeness_pct" in stats
        assert 0.0 <= stats["completeness_pct"] <= 100.0


def test_analytics_overview_endpoint(client: TestClient):
    """Verifies GET /api/v1/analytics/overview returns aggregate high-level metrics."""
    res = client.get("/api/v1/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_investigations"] >= 4
    assert isinstance(data["combustion_regimes"], dict)


def test_missing_data_analysis_endpoint(client: TestClient):
    """Verifies GET /api/v1/analytics/missing-data-analysis focuses on physical measurement completeness."""
    res = client.get("/api/v1/analytics/missing-data-analysis")
    assert res.status_code == 200
    data = res.json()
    assert "missing_data_matrix" in data
    matrix = data["missing_data_matrix"]
    assert "chamber_pressure_pa" in matrix or any("pressure" in k for k in matrix)
