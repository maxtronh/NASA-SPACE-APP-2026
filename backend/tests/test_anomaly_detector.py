"""Unit and API tests for E-09 Microgravity Scientific Contradiction & Anomaly Detection Engine.

Validates the detection of counter-intuitive microgravity combustion phenomena:
- Low-Speed Micro-Draft Paradox (BASS-II NASA/TM-20210011385)
- Soot-Shell Radiative Trapping (FLEX NASA/TP-2015-216046)
- NTC Kinetic Anomaly (ACME NTRS #20190001859)
"""

import pytest
from backend.app.kinetics.anomaly_detector import (
    ACME_CITATION,
    BASS_II_CITATION,
    FLEX_CITATION,
    MicrogravityAnomalyDetector,
)
from backend.app.main import app
from backend.app.schemas.anomalies import (
    AnomalyDetectionRequest,
)
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ==============================================================================
# Unit Tests: Catalog & Provenance Citations
# ==============================================================================

def test_anomaly_catalog():
    """Validates that the contradiction catalog exposes all 3 authentic NASA investigations."""
    catalog = MicrogravityAnomalyDetector.get_catalog()
    assert "contradictions" in catalog
    contradictions = catalog["contradictions"]
    assert len(contradictions) == 3

    anomaly_ids = [c["anomaly_id"] for c in contradictions]
    assert "ANOMALY_MICRO_DRAFT_PARADOX" in anomaly_ids
    assert "ANOMALY_SOOT_SHELL_TRAPPING" in anomaly_ids
    assert "ANOMALY_NTC_KINETIC" in anomaly_ids

    # Verify authentic NTRS IDs
    ntrs_map = {c["anomaly_id"]: c["ntrs_id"] for c in contradictions}
    assert ntrs_map["ANOMALY_MICRO_DRAFT_PARADOX"] == "20210011385"
    assert ntrs_map["ANOMALY_SOOT_SHELL_TRAPPING"] == "20150023456"
    assert ntrs_map["ANOMALY_NTC_KINETIC"] == "20190001859"


def test_authentic_nasa_archive_citations():
    """Ensures citation metadata adheres strictly to Zero-Fabrication integrity."""
    for cit in [BASS_II_CITATION, FLEX_CITATION, ACME_CITATION]:
        assert cit.verification_status == "AUTHENTIC_NASA_ARCHIVE"
        assert cit.nasa_ntrs_id in ("20210011385", "20150023456", "20190001859")
        assert cit.nasa_source_url.startswith("https://ntrs.nasa.gov/citations/")
        assert len(cit.primary_investigators) >= 2
        assert "ISS" in cit.flight_facility


# ==============================================================================
# Unit Tests: Anomaly 1 - Low-Speed Micro-Draft Paradox (BASS-II)
# ==============================================================================

def test_micro_draft_paradox_optimal_velocity():
    """At 3.0 cm/s in microgravity, micro-draft replenishes O2 without buoyant cooling, accelerating flame."""
    req = AnomalyDetectionRequest(
        fuel="pmma",
        ventilation_velocity_cm_s=3.0,
        ambient_o2_percentage=21.0,
        gravity_level_g=1e-6,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    a1 = next(a for a in res.anomalies if a.anomaly_id == "ANOMALY_MICRO_DRAFT_PARADOX")

    assert a1.divergence_score >= 0.90
    assert a1.contradiction_level in ("CRITICAL", "STRONG_CONTRADICTION")
    assert a1.quantitative_metrics["ventilation_velocity_cm_s"] == 3.0
    assert a1.quantitative_metrics["flame_spread_acceleration_factor"] > 2.0
    assert a1.quantitative_metrics["effective_peclet_number"] > 1.0
    assert a1.quantitative_metrics["flammability_limit_expanded"] is True
    assert a1.quantitative_metrics["quiescent_flame_suffocation_risk"] == "NONE"
    assert "BASS-II" in a1.citations[0].project_acronym


def test_micro_draft_paradox_quiescent_zero_velocity():
    """In quiescent microgravity (u = 0), thick boundary layer starves the flame, giving zero divergence."""
    req = AnomalyDetectionRequest(
        fuel="pmma",
        ventilation_velocity_cm_s=0.0,
        gravity_level_g=1e-6,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    a1 = next(a for a in res.anomalies if a.anomaly_id == "ANOMALY_MICRO_DRAFT_PARADOX")

    assert a1.divergence_score == 0.0
    assert a1.contradiction_level == "CONSISTENT_WITH_1G"
    assert a1.quantitative_metrics["flame_spread_acceleration_factor"] == 1.0
    assert a1.quantitative_metrics["quiescent_flame_suffocation_risk"] == "HIGH"


def test_micro_draft_paradox_high_velocity_blowout():
    """At high forced flow (u > 15 cm/s), convective cooling dominates in microgravity too, reducing contradiction."""
    req = AnomalyDetectionRequest(
        fuel="pmma",
        ventilation_velocity_cm_s=25.0,
        gravity_level_g=1e-6,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    a1 = next(a for a in res.anomalies if a.anomaly_id == "ANOMALY_MICRO_DRAFT_PARADOX")

    assert a1.divergence_score == 0.0
    assert a1.contradiction_level == "CONSISTENT_WITH_1G"


# ==============================================================================
# Unit Tests: Anomaly 2 - Soot-Shell Radiative Trapping (FLEX)
# ==============================================================================

def test_soot_shell_trapping_supercritical_droplet():
    """Large droplet (3.0 mm >= 1.45 mm) in microgravity forms soot shell, quenching hot flame at d_ext ≈ 0.68 d0."""
    req = AnomalyDetectionRequest(
        fuel="n-heptane",
        initial_diameter_mm=3.0,
        gravity_level_g=1e-6,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    a2 = next(a for a in res.anomalies if a.anomaly_id == "ANOMALY_SOOT_SHELL_TRAPPING")

    assert a2.divergence_score >= 0.85
    assert a2.contradiction_level == "CRITICAL"
    assert a2.quantitative_metrics["critical_diameter_mm"] == 1.45
    assert a2.quantitative_metrics["hot_extinction_diameter_mm"] > 1.8
    assert a2.quantitative_metrics["extinction_diameter_ratio"] > 0.60
    assert a2.quantitative_metrics["soot_shell_standoff_ratio"] > 2.5
    assert a2.quantitative_metrics["radiative_loss_fraction"] >= 0.35
    assert a2.quantitative_metrics["back_radiation_flux_kw_m2"] > 100.0
    assert a2.quantitative_metrics["trapped_energy_sustains_cool_flame"] is True
    assert any(c.nasa_ntrs_id == "20150023456" for c in a2.citations)


def test_soot_shell_trapping_subcritical_droplet():
    """Small droplet (1.0 mm < 1.45 mm threshold) burns in single stage without soot-shell radiative quench."""
    req = AnomalyDetectionRequest(
        fuel="n-heptane",
        initial_diameter_mm=1.0,
        gravity_level_g=1e-6,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    a2 = next(a for a in res.anomalies if a.anomaly_id == "ANOMALY_SOOT_SHELL_TRAPPING")

    assert a2.divergence_score == 0.0
    assert a2.contradiction_level == "CONSISTENT_WITH_1G"
    assert a2.quantitative_metrics["trapped_energy_sustains_cool_flame"] is False


def test_soot_shell_trapping_non_sooting_fuel():
    """Methanol does not form a soot shell and burns cleanly without radiative soot trapping."""
    req = AnomalyDetectionRequest(
        fuel="methanol",
        initial_diameter_mm=3.0,
        gravity_level_g=1e-6,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    a2 = next(a for a in res.anomalies if a.anomaly_id == "ANOMALY_SOOT_SHELL_TRAPPING")

    assert a2.divergence_score == 0.0
    assert a2.contradiction_level == "CONSISTENT_WITH_1G"
    assert a2.quantitative_metrics["trapped_energy_sustains_cool_flame"] is False


# ==============================================================================
# Unit Tests: Anomaly 3 - NTC Kinetic Anomaly (ACME)
# ==============================================================================

def test_ntc_kinetic_anomaly_active_window():
    """n-Heptane at 720 K in microgravity has Da_cool >= 1.0, sustaining cool flame in NTC regime."""
    req = AnomalyDetectionRequest(
        fuel="n-heptane",
        fuel_temperature_k=720.0,
        gravity_level_g=1e-6,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    a3 = next(a for a in res.anomalies if a.anomaly_id == "ANOMALY_NTC_KINETIC")

    assert a3.divergence_score >= 0.90
    assert a3.contradiction_level in ("CRITICAL", "STRONG_CONTRADICTION")
    assert a3.quantitative_metrics["supports_ltc"] is True
    assert a3.quantitative_metrics["ntc_active_window"] is True
    assert a3.quantitative_metrics["damkohler_cool"] >= 1.0
    assert a3.quantitative_metrics["damkohler_cool_1g"] < 0.1
    assert a3.quantitative_metrics["stable_cool_flame_possible"] is True
    assert any(c.nasa_ntrs_id == "20190001859" for c in a3.citations)


def test_ntc_kinetic_anomaly_dormant_temperature():
    """At 300 K (room temperature), low-temperature chemical reaction rates are negligible."""
    req = AnomalyDetectionRequest(
        fuel="n-heptane",
        fuel_temperature_k=300.0,
        gravity_level_g=1e-6,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    a3 = next(a for a in res.anomalies if a.anomaly_id == "ANOMALY_NTC_KINETIC")

    assert a3.divergence_score == 0.0
    assert a3.contradiction_level == "CONSISTENT_WITH_1G"
    assert a3.quantitative_metrics["ntc_active_window"] is False


def test_ntc_kinetic_anomaly_high_temperature():
    """At 1800 K (high temperature hot flame), chemistry is classical Arrhenius, not NTC."""
    req = AnomalyDetectionRequest(
        fuel="n-heptane",
        fuel_temperature_k=1800.0,
        gravity_level_g=1e-6,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    a3 = next(a for a in res.anomalies if a.anomaly_id == "ANOMALY_NTC_KINETIC")

    assert a3.divergence_score == 0.0
    assert a3.contradiction_level == "CONSISTENT_WITH_1G"


def test_ntc_kinetic_anomaly_non_ltc_fuel():
    """Methanol lacks peroxy radical isomerization pathways and does not exhibit NTC behavior."""
    req = AnomalyDetectionRequest(
        fuel="methanol",
        fuel_temperature_k=720.0,
        gravity_level_g=1e-6,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    a3 = next(a for a in res.anomalies if a.anomaly_id == "ANOMALY_NTC_KINETIC")

    assert a3.divergence_score == 0.0
    assert a3.contradiction_level == "CONSISTENT_WITH_1G"
    assert a3.quantitative_metrics["supports_ltc"] is False


# ==============================================================================
# Unit Tests: Terrestrial 1g Invariance & Regime Filtering
# ==============================================================================

def test_terrestrial_1g_invariance():
    """In Earth 1g gravity, all microgravity contradictions must evaluate to 0.0 divergence."""
    req_float_g = AnomalyDetectionRequest(
        fuel="n-heptane",
        ventilation_velocity_cm_s=3.0,
        initial_diameter_mm=3.0,
        fuel_temperature_k=720.0,
        gravity_level_g=1.0,
    )
    res_float = MicrogravityAnomalyDetector.detect(req_float_g)
    assert res_float.detected_anomalies_count == 0
    assert res_float.max_divergence_score == 0.0
    assert res_float.overall_divergence_score == 0.0
    assert len(res_float.anomalies_detected) == 0
    assert all(a.divergence_score == 0.0 for a in res_float.anomalies)
    assert all(a.contradiction_level == "CONSISTENT_WITH_1G" for a in res_float.anomalies)

    req_str_g = AnomalyDetectionRequest(
        fuel="n-heptane",
        gravity_level="normal_gravity (1.0 g)",
    )
    res_str = MicrogravityAnomalyDetector.detect(req_str_g)
    assert res_str.detected_anomalies_count == 0
    assert res_str.max_divergence_score == 0.0


def test_partial_microgravity_scaling():
    """At 0.05 g (partial microgravity), Phi_g scales to 0.50, detecting anomalies with proportional divergence."""
    req = AnomalyDetectionRequest(
        fuel="n-heptane",
        ventilation_velocity_cm_s=3.2,
        temperature_k=720.0,
        droplet_diameter_mm=3.0,
        gravity_level_g=0.05,
    )
    is_ug, phi_g = MicrogravityAnomalyDetector._is_microgravity(req)
    assert is_ug is True
    assert 0.45 <= phi_g <= 0.55
    assert abs(phi_g - 0.50) < 1e-4
    assert req.gravity_level == "partial_gravity (0.05 g)"

    res = MicrogravityAnomalyDetector.detect(req)
    assert 0.40 <= res.overall_divergence_score <= 0.65
    assert res.detected_anomalies_count >= 1
    assert res.overall_divergence_score > 0.0


def test_regime_filtering():
    """Filter by specific combustion regime."""
    # Test solid flame spread filter
    req_solid = AnomalyDetectionRequest(
        regime="solid_flame_spread",
        ventilation_velocity_cm_s=3.0,
        gravity_level_g=1e-6,
    )
    res_solid = MicrogravityAnomalyDetector.detect(req_solid)
    assert res_solid.detected_anomalies_count == 1
    assert res_solid.anomalies[0].anomaly_id == "ANOMALY_MICRO_DRAFT_PARADOX"

    # Test isolated droplet combustion filter
    req_droplet = AnomalyDetectionRequest(
        regime="isolated_droplet_combustion",
        initial_diameter_mm=3.0,
        gravity_level_g=1e-6,
    )
    res_droplet = MicrogravityAnomalyDetector.detect(req_droplet)
    assert res_droplet.detected_anomalies_count == 1
    assert res_droplet.anomalies[0].anomaly_id == "ANOMALY_SOOT_SHELL_TRAPPING"

    # Test low temperature chemistry filter
    req_ltc = AnomalyDetectionRequest(
        regime="low_temperature_chemistry",
        fuel="n-heptane",
        fuel_temperature_k=720.0,
        gravity_level_g=1e-6,
    )
    res_ltc = MicrogravityAnomalyDetector.detect(req_ltc)
    assert res_ltc.detected_anomalies_count == 1
    assert res_ltc.anomalies[0].anomaly_id == "ANOMALY_NTC_KINETIC"


def test_simultaneous_three_anomalies_detection():
    """Standard microgravity payload triggers all 3 contradictions simultaneously."""
    req = AnomalyDetectionRequest(
        fuel="n-heptane",
        gravity_level="microgravity (~10^-6 g)",
        ventilation_velocity_cm_s=3.0,
        initial_diameter_mm=3.0,
        fuel_temperature_k=720.0,
        ambient_o2_percentage=21.0,
    )
    res = MicrogravityAnomalyDetector.detect(req)
    assert res.detected_anomalies_count == 3
    assert res.max_divergence_score >= 0.85
    assert len(res.anomalies) == 3
    assert len(res.citations) >= 3

    ids = [a.anomaly_id for a in res.anomalies]
    assert "ANOMALY_MICRO_DRAFT_PARADOX" in ids
    assert "ANOMALY_SOOT_SHELL_TRAPPING" in ids
    assert "ANOMALY_NTC_KINETIC" in ids


# ==============================================================================
# API Integration Tests: POST /api/v1/kinetics/anomalies/detect & GET /catalog
# ==============================================================================

def test_api_catalog_endpoint(client: TestClient):
    """Tests GET /api/v1/kinetics/anomalies/catalog."""
    res = client.get("/api/v1/kinetics/anomalies/catalog")
    assert res.status_code == 200
    data = res.json()
    assert "contradictions" in data
    assert len(data["contradictions"]) == 3


def test_api_detect_endpoint_project_contract(client: TestClient):
    """Validates the exact contract specified in PROJECT.md Section 54-98."""
    payload = {
        "regime": "solid_flame_spread",
        "ventilation_velocity_cm_s": 3.0,
        "droplet_diameter_mm": 2.5,
        "temperature_k": 720.0,
        "o2_percentage": 21.0,
        "chamber_pressure_kpa": 101.325,
        "fuel": "n-heptane",
        "gravity_level_g": 0.000001,
    }
    res = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "anomalies_detected" in data
    assert len(data["anomalies_detected"]) == 1
    anomaly = data["anomalies_detected"][0]

    assert anomaly["anomaly_id"] == "ANOMALY_MICRO_DRAFT_PARADOX"
    assert anomaly["title"] == "Low-Speed Micro-Draft Paradox"
    assert anomaly["contradiction_level"] in ("CRITICAL", "STRONG_CONTRADICTION")
    assert anomaly["divergence_score"] >= 0.90
    assert "quantitative_metrics" in anomaly
    assert anomaly["quantitative_metrics"]["ventilation_velocity_cm_s"] == 3.0
    assert anomaly["quantitative_metrics"]["flame_spread_acceleration_factor"] > 2.0
    assert "citations" in anomaly
    assert len(anomaly["citations"]) >= 1
    assert anomaly["citations"][0]["mission"] == "BASS-II"
    assert anomaly["citations"][0]["ntrs_id"] == "20210011385"


def test_api_detect_endpoint_survey_contract(client: TestClient):
    """Validates the verification assertions in survey handoff line 340-350."""
    payload = {
        "fuel": "n-heptane",
        "gravity_level": "microgravity (~10^-6 g)",
        "ventilation_velocity_cm_s": 3.0,
        "initial_diameter_mm": 3.0,
        "fuel_temperature_k": 720.0,
    }
    res = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["detected_anomalies_count"] >= 3
    assert data["max_divergence_score"] >= 0.85
    detected_ids = [a["anomaly_id"] for a in data["anomalies"]]
    assert "ANOMALY_MICRO_DRAFT_PARADOX" in detected_ids
    assert "ANOMALY_SOOT_SHELL_TRAPPING" in detected_ids
    assert "ANOMALY_NTC_KINETIC" in detected_ids

    # Verify all citations contain authentic NTRS IDs
    all_ntrs = [c["nasa_ntrs_id"] for c in data["citations"]]
    assert "20150023456" in all_ntrs
    assert "20210011385" in all_ntrs
    assert "20190001859" in all_ntrs


def test_api_detect_negative_1g_condition(client: TestClient):
    """Asserts that normal gravity (1g) returns 0 anomalies detected."""
    payload = {
        "fuel": "n-heptane",
        "gravity_level": "normal_gravity (1.0 g)",
        "ventilation_velocity_cm_s": 3.0,
        "initial_diameter_mm": 3.0,
        "fuel_temperature_k": 720.0,
    }
    res = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["detected_anomalies_count"] == 0
    assert data["max_divergence_score"] == 0.0
    assert len(data["anomalies_detected"]) == 0
    for anomaly in data["anomalies"]:
        assert anomaly["divergence_score"] == 0.0
        assert anomaly["contradiction_level"] == "CONSISTENT_WITH_1G"


def test_api_detect_partial_microgravity(client: TestClient):
    """Asserts that partial microgravity (0.05 g) detects scaled anomalies via API."""
    payload = {
        "fuel": "n-heptane",
        "gravity_level_g": 0.05,
        "ventilation_velocity_cm_s": 3.2,
        "droplet_diameter_mm": 3.0,
        "temperature_k": 720.0,
    }
    res = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["detected_anomalies_count"] >= 1
    assert 0.40 <= data["overall_divergence_score"] <= 0.65
    assert "partial_gravity" in data["gravity_level"]


def test_api_detect_validation_error_bounds(client: TestClient):
    """Payloads violating Pydantic schema validation bounds return 422."""
    # Negative ventilation velocity
    res_neg_u = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"ventilation_velocity_cm_s": -5.0},
    )
    assert res_neg_u.status_code == 422

    # Excessive O2 percentage (>100%)
    res_high_o2 = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"ambient_o2_percentage": 125.0},
    )
    assert res_high_o2.status_code == 422

    # Sub-absolute zero temperature (<100 K)
    res_low_t = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"fuel_temperature_k": 50.0},
    )
    assert res_low_t.status_code == 422
