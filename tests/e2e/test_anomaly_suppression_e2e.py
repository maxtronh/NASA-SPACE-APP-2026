"""
End-to-End (E2E) Test Suite for Autonomous Scientific Discovery (E-09)
and Interactive Cabin Fire Suppression Simulator (E-12) — Milestone M4.

Full 4-tier opaque-box test architecture as specified in TEST_INFRA.md:
- Tier 1: Feature Coverage (>=5 tests per feature domain: Anomaly Detection & Cabin Suppression)
- Tier 2: Boundary & Corner Cases (>=5 tests per feature domain)
- Tier 3: Cross-Feature Interactions & Action Combinations
- Tier 4: Real-World Spacecraft Application Scenarios (all 5 scenarios from TEST_INFRA.md)

Scientific Provenance:
- BASS-II: NASA/TM-20210011385 (Solid flame spread paradox in Microgravity Science Glovebox)
- FLEX / FLEX-2: NASA/TP-2015-216046 / NTRS #20150023456 (Soot-shell radiative quench)
- ACME: NTRS #20190001859 (NTC peroxy radical chemistry in CIR)
- NASA-STD-6001B: Spacecraft flammability and fire suppression standards
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provides a shared FastAPI TestClient instance."""
    with TestClient(app) as c:
        yield c


# ==============================================================================
# Tier 1 — Feature Coverage: Feature Domain A (Anomaly Detection E-09)
# ==============================================================================


def test_tier1_anomaly_micro_draft_paradox_detection(client: TestClient):
    """Tier 1: Happy path detection of Low-Speed Micro-Draft Paradox (BASS-II).

    In microgravity, low concurrent draft (1-5 cm/s) widens flammability limits and
    accelerates solid flame spread up to 3x without buoyant cooling.
    """
    payload = {
        "regime": "solid_flame_spread",
        "fuel": "pmma",
        "ventilation_velocity_cm_s": 3.0,
        "ambient_o2_percentage": 21.0,
        "gravity_level_g": 0.000001,
        "chamber_pressure_kpa": 101.325,
    }
    response = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["detected_anomalies_count"] >= 1
    assert data["overall_divergence_score"] >= 0.85
    assert data["primary_contradiction"] == "ANOMALY_MICRO_DRAFT_PARADOX"

    # Find the anomaly
    anomaly = next(
        a for a in data["anomalies"] if a["anomaly_id"] == "ANOMALY_MICRO_DRAFT_PARADOX"
    )
    assert anomaly["title"] == "Low-Speed Micro-Draft Paradox"
    assert anomaly["regime"] == "solid_flame_spread"
    assert anomaly["divergence_score"] >= 0.90
    assert anomaly["contradiction_level"] in ("CRITICAL", "STRONG_CONTRADICTION")

    metrics = anomaly["quantitative_metrics"]
    assert metrics["ventilation_velocity_cm_s"] == 3.0
    assert metrics["flame_spread_acceleration_factor"] > 2.0
    assert metrics["effective_peclet_number"] > 1.0
    assert metrics["flammability_limit_expanded"] is True

    # Check authentic BASS-II citation
    citations = anomaly["citations"]
    assert len(citations) >= 1
    bass_cit = citations[0]
    assert bass_cit["mission"] == "BASS-II"
    assert bass_cit["ntrs_id"] == "20210011385"
    assert bass_cit["verification_status"] == "AUTHENTIC_NASA_ARCHIVE"
    assert "Microgravity Science Glovebox" in bass_cit["flight_facility"]


def test_tier1_anomaly_soot_shell_radiative_trapping_detection(client: TestClient):
    """Tier 1: Happy path detection of Soot-Shell Radiative Trapping (FLEX / FLEX-2).

    Non-buoyant spherical soot cloud forms concentric radiation barrier quenching
    the visible hot flame at d_ext ≈ 0.68 d0 while trapping heat for cool flame.
    """
    payload = {
        "regime": "isolated_droplet_combustion",
        "fuel": "n-heptane",
        "droplet_diameter_mm": 3.0,
        "gravity_level": "microgravity (~10^-6 g)",
        "chamber_pressure_kpa": 101.325,
    }
    response = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["detected_anomalies_count"] >= 1
    anomaly = next(
        a for a in data["anomalies"] if a["anomaly_id"] == "ANOMALY_SOOT_SHELL_TRAPPING"
    )
    assert anomaly["title"] == "Soot-Shell Radiative Trapping"
    assert anomaly["divergence_score"] >= 0.85
    assert anomaly["contradiction_level"] == "CRITICAL"

    metrics = anomaly["quantitative_metrics"]
    assert metrics["critical_diameter_mm"] == 1.45
    assert metrics["extinction_diameter_ratio"] >= 0.60
    assert metrics["hot_extinction_diameter_mm"] > 1.8
    assert metrics["radiative_loss_fraction"] >= 0.35
    assert metrics["back_radiation_flux_kw_m2"] > 100.0
    assert metrics["trapped_energy_sustains_cool_flame"] is True

    # Check authentic FLEX citation
    citations = anomaly["citations"]
    flex_cit = next(c for c in citations if c["ntrs_id"] == "20150023456")
    assert flex_cit["mission"] == "FLEX"
    assert flex_cit["verification_status"] == "AUTHENTIC_NASA_ARCHIVE"
    assert "CIR" in flex_cit["flight_facility"]


def test_tier1_anomaly_ntc_kinetic_anomaly_detection(client: TestClient):
    """Tier 1: Happy path detection of NTC Kinetic Anomaly (ACME / FLEX).

    Negative Temperature Coefficient peroxy radical chemistry (650-800 K) under
    diffusive microgravity residence times (Da_cool >= 1.0) sustains cool flames.
    """
    payload = {
        "regime": "low_temperature_chemistry",
        "fuel": "n-heptane",
        "temperature_k": 720.0,
        "gravity_level_g": 1e-6,
    }
    response = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["detected_anomalies_count"] >= 1
    anomaly = next(
        a for a in data["anomalies"] if a["anomaly_id"] == "ANOMALY_NTC_KINETIC"
    )
    assert anomaly["title"] == "NTC Kinetic Anomaly"
    assert anomaly["divergence_score"] >= 0.90
    assert anomaly["contradiction_level"] in ("CRITICAL", "STRONG_CONTRADICTION")

    metrics = anomaly["quantitative_metrics"]
    assert metrics["supports_ltc"] is True
    assert metrics["ntc_active_window"] is True
    assert metrics["damkohler_cool"] >= 1.0
    assert metrics["damkohler_cool_1g"] < 0.1
    assert metrics["stable_cool_flame_possible"] is True

    # Check authentic ACME citation
    citations = anomaly["citations"]
    acme_cit = next(c for c in citations if c["ntrs_id"] == "20190001859")
    assert acme_cit["mission"] == "ACME"
    assert acme_cit["verification_status"] == "AUTHENTIC_NASA_ARCHIVE"


def test_tier1_anomaly_explainability_and_ntrs_citations(client: TestClient):
    """Tier 1: Verifies comprehensive explainability mechanisms and authentic NTRS citations."""
    payload = {
        "fuel": "n-heptane",
        "ventilation_velocity_cm_s": 3.2,
        "initial_diameter_mm": 3.0,
        "fuel_temperature_k": 720.0,
        "gravity_level": "microgravity (~10^-6 g)",
    }
    response = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    # All three anomalies detected in full-spectrum request
    assert data["detected_anomalies_count"] == 3
    assert len(data["anomalies"]) == 3

    # Each anomaly must contain complete narrative explainability
    for anomaly in data["anomalies"]:
        assert len(anomaly["mechanism"]) > 20
        assert len(anomaly["classical_1g_behavior"]) > 20
        assert len(anomaly["microgravity_behavior"]) > 20
        assert len(anomaly["citations"]) >= 1

    # Unique citations list across all three authentic investigations
    ntrs_ids = [c["nasa_ntrs_id"] for c in data["citations"]]
    assert "20210011385" in ntrs_ids  # BASS-II
    assert "20150023456" in ntrs_ids  # FLEX
    assert "20190001859" in ntrs_ids  # ACME

    for cit in data["citations"]:
        assert cit["verification_status"] == "AUTHENTIC_NASA_ARCHIVE"
        assert cit["nasa_source_url"].startswith("https://ntrs.nasa.gov/citations/")
        assert len(cit["primary_investigators"]) >= 2


def test_tier1_anomaly_overall_divergence_score_calculation(client: TestClient):
    """Tier 1: Verifies overall divergence score scaling and summary string formatting."""
    payload = {
        "fuel": "n-heptane",
        "ventilation_velocity_cm_s": 3.2,
        "droplet_diameter_mm": 3.0,
        "temperature_k": 720.0,
        "gravity_level_g": 1e-6,
    }
    response = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert 0.0 <= data["overall_divergence_score"] <= 1.0
    assert data["overall_divergence_score"] == data["max_divergence_score"]
    assert "Detected 3 microgravity combustion contradictions" in data["summary"]
    assert data["primary_contradiction"] in (
        "ANOMALY_MICRO_DRAFT_PARADOX",
        "ANOMALY_SOOT_SHELL_TRAPPING",
        "ANOMALY_NTC_KINETIC",
    )


def test_tier1_anomaly_catalog_endpoint(client: TestClient):
    """Tier 1: Verifies GET /api/v1/kinetics/anomalies/catalog endpoint."""
    response = client.get("/api/v1/kinetics/anomalies/catalog")
    assert response.status_code == 200, response.text
    data = response.json()

    assert "contradictions" in data
    contradictions = data["contradictions"]
    assert len(contradictions) == 3

    catalog_ids = {c["anomaly_id"]: c for c in contradictions}
    assert "ANOMALY_MICRO_DRAFT_PARADOX" in catalog_ids
    assert "ANOMALY_SOOT_SHELL_TRAPPING" in catalog_ids
    assert "ANOMALY_NTC_KINETIC" in catalog_ids

    assert catalog_ids["ANOMALY_MICRO_DRAFT_PARADOX"]["ntrs_id"] == "20210011385"
    assert catalog_ids["ANOMALY_SOOT_SHELL_TRAPPING"]["ntrs_id"] == "20150023456"
    assert catalog_ids["ANOMALY_NTC_KINETIC"]["ntrs_id"] == "20190001859"


# ==============================================================================
# Tier 1 — Feature Coverage: Feature Domain B (Safety Fire Suppression E-12)
# ==============================================================================


def test_tier1_suppression_ventilation_damper_isolation(client: TestClient):
    """Tier 1: Happy path simulation of Ventilation Damper Isolation.

    Forced airflow shutdown reduces u_vent from 3.0 cm/s to diffusion floor (0.01 cm/s),
    triggering radiative extinction at ~14.5s.
    """
    payload = {
        "fuel": "n-heptane",
        "initial_fuel_temperature_k": 720.0,
        "initial_o2_percentage": 21.0,
        "initial_ventilation_velocity_cm_s": 3.0,
        "damper_isolated": True,
        "chemical_agent_released": False,
        "n2_flooding_active": False,
        "simulation_duration_s": 30.0,
        "time_step_s": 0.5,
        "restart_ventilation_velocity_cm_s": 3.0,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["actions_applied"] == ["DAMPER_ISOLATION"]
    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] == 14.5
    assert data["final_ventilation_velocity_cm_s"] == 0.01
    assert "radiative heat loss extinction" in data["extinction_mechanism"]

    # Trapped heat: fuel stays hot, so ventilation restart is unsafe
    assert data["final_temperature_k"] > 350.0
    assert data["residual_radical_heat_release_w"] > 0.0
    assert data["safe_to_restart_ventilation"] is False
    assert data["rekindle_risk_level"] in (
        "REKINDLE_WARNING",
        "CRITICAL_REKINDLE_HAZARD",
    )
    assert "DO NOT restart ventilation" in data["safety_advisory"]
    assert "DAMPER_ISOLATION_STANDBY" in data["audit_message"]


def test_tier1_suppression_fk5112_chemical_agent_release(client: TestClient):
    """Tier 1: Happy path simulation of FK-5-1-12 Chemical Agent Release.

    Catalytic radical scavenging rapidly collapses heat release rate within ~1.1-1.5s
    and endothermically cools fuel below flash point.
    """
    payload = {
        "fuel": "n-heptane",
        "initial_fuel_temperature_k": 720.0,
        "chemical_agent_released": True,
        "chemical_agent_type": "FK-5-1-12",
        "damper_isolated": False,
        "n2_flooding_active": False,
        "simulation_duration_s": 30.0,
        "time_step_s": 0.5,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["actions_applied"] == ["CHEMICAL_AGENT_RELEASE"]
    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] <= 2.0
    assert data["residual_radical_heat_release_w"] == 0.0
    assert data["final_temperature_k"] <= 315.0
    assert data["damkohler_cool_final"] == 0.0
    assert data["rekindle_probability_restart"] == 0.0
    assert data["rekindle_risk_level"] == "INERT"
    assert data["safe_to_restart_ventilation"] is True
    assert "Safe to restore ventilation" in data["safety_advisory"]
    assert "SUPPRESSION_SUCCESS" in data["audit_message"]


def test_tier1_suppression_halon_1301_chemical_agent_release(client: TestClient):
    """Tier 1: Happy path simulation of Halon 1301 Chemical Agent Release."""
    payload = {
        "fuel": "n-octane",
        "initial_fuel_temperature_k": 750.0,
        "chemical_agent_released": True,
        "chemical_agent_type": "Halon 1301",
        "damper_isolated": False,
        "simulation_duration_s": 20.0,
        "time_step_s": 0.5,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["actions_applied"] == ["CHEMICAL_AGENT_RELEASE"]
    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] == 1.5
    assert data["rekindle_risk_level"] == "INERT"
    assert data["residual_radical_heat_release_w"] == 0.0
    assert data["safe_to_restart_ventilation"] is True
    assert "Halon 1301 successfully scavenged" in data["safety_advisory"]


def test_tier1_suppression_n2_chamber_flooding(client: TestClient):
    """Tier 1: Happy path simulation of Nitrogen (N2) Chamber Flooding.

    Hypobaric dilution reduces cabin O2 below MOC (~11.8% for alkanes), achieving
    extinction at ~7.2s.
    """
    payload = {
        "fuel": "n-heptane",
        "initial_fuel_temperature_k": 720.0,
        "initial_o2_percentage": 21.0,
        "n2_flooding_active": True,
        "n2_target_o2_percentage": 9.5,
        "damper_isolated": False,
        "chemical_agent_released": False,
        "simulation_duration_s": 30.0,
        "time_step_s": 0.5,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["actions_applied"] == ["N2_FLOODING"]
    assert data["extinction_achieved"] is True
    assert 6.0 <= data["transient_extinction_time_s"] <= 8.5
    assert data["final_o2_percentage"] <= 10.0
    assert "N2_FLOODING_EXTINCTION" in data["audit_message"]
    assert "Maintain inert N2 blanket" in data["safety_advisory"]


def test_tier1_suppression_transient_extinction_dynamics(client: TestClient):
    """Tier 1: Validates transient decay curve metrics (t_ext, Q_res, Da_cool, P_rekindle)."""
    payload = {
        "fuel": "n-heptane",
        "initial_fuel_temperature_k": 720.0,
        "damper_isolated": True,
        "chemical_agent_released": True,
        "chemical_agent_type": "FK-5-1-12",
        "simulation_duration_s": 15.0,
        "time_step_s": 0.5,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    curve = data["decay_curve"]
    assert len(curve) == 31  # 15.0 / 0.5 + 1
    assert curve[0]["time_s"] == 0.0
    assert curve[-1]["time_s"] == 15.0

    # Ensure physical trajectories in decay points
    for pt in curve:
        assert pt["temperature_k"] >= 250.0
        assert pt["heat_release_rate_kw"] >= 0.0
        assert pt["residual_radical_hrr_w"] >= 0.0
        assert 0.0 <= pt["o2_percentage"] <= 25.0
        assert 0.0 <= pt["ventilation_velocity_cm_s"] <= 5.0
        assert 0.0 <= pt["agent_concentration_vol_pct"] <= 7.0
        assert pt["damkohler_cool"] >= 0.0
        assert 0.0 <= pt["rekindle_probability"] <= 1.0


# ==============================================================================
# Tier 2 — Boundary & Corner Cases: Domain A (Anomaly Detection)
# ==============================================================================


def test_tier2_anomaly_zero_ventilation_velocity_suffocation(client: TestClient):
    """Tier 2: At zero ventilation velocity (quiescent microgravity), thick boundary layer suffocates flame."""
    payload = {
        "regime": "solid_flame_spread",
        "fuel": "pmma",
        "ventilation_velocity_cm_s": 0.0,
        "gravity_level_g": 1e-6,
    }
    response = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    anomaly = next(
        a for a in data["anomalies"] if a["anomaly_id"] == "ANOMALY_MICRO_DRAFT_PARADOX"
    )
    assert anomaly["divergence_score"] == 0.0
    assert anomaly["contradiction_level"] == "CONSISTENT_WITH_1G"
    assert anomaly["quantitative_metrics"]["quiescent_flame_suffocation_risk"] == "HIGH"
    assert anomaly["quantitative_metrics"]["flame_spread_acceleration_factor"] == 1.0


def test_tier2_anomaly_high_ventilation_velocity_blowout(client: TestClient):
    """Tier 2: High draft speeds (u > 15 cm/s) cause convective cooling in microgravity, reducing divergence."""
    payload = {
        "regime": "solid_flame_spread",
        "fuel": "pmma",
        "ventilation_velocity_cm_s": 25.0,
        "gravity_level_g": 1e-6,
    }
    response = client.post("/api/v1/kinetics/anomalies/detect", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    anomaly = next(
        a for a in data["anomalies"] if a["anomaly_id"] == "ANOMALY_MICRO_DRAFT_PARADOX"
    )
    assert anomaly["divergence_score"] == 0.0
    assert anomaly["contradiction_level"] == "CONSISTENT_WITH_1G"


def test_tier2_anomaly_temperature_boundaries_ambient_vs_extreme(client: TestClient):
    """Tier 2: Temperature boundaries (300 K ambient, 1800 K hot flame, 650 K / 800 K NTC window)."""
    # 1. Room temperature 300 K: LTC inactive
    res_cold = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"fuel": "n-heptane", "temperature_k": 300.0, "gravity_level_g": 1e-6},
    )
    assert res_cold.status_code == 200
    a_cold = next(
        a
        for a in res_cold.json()["anomalies"]
        if a["anomaly_id"] == "ANOMALY_NTC_KINETIC"
    )
    assert a_cold["divergence_score"] == 0.0
    assert a_cold["quantitative_metrics"]["ntc_active_window"] is False

    # 2. Extreme hot flame 1800 K: Single-stage classical combustion dominates
    res_hot = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"fuel": "n-heptane", "temperature_k": 1800.0, "gravity_level_g": 1e-6},
    )
    assert res_hot.status_code == 200
    a_hot = next(
        a
        for a in res_hot.json()["anomalies"]
        if a["anomaly_id"] == "ANOMALY_NTC_KINETIC"
    )
    assert a_hot["divergence_score"] == 0.0

    # 3. NTC lower boundary 650 K: LTC active
    res_650 = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"fuel": "n-heptane", "temperature_k": 650.0, "gravity_level_g": 1e-6},
    )
    assert res_650.status_code == 200
    a_650 = next(
        a
        for a in res_650.json()["anomalies"]
        if a["anomaly_id"] == "ANOMALY_NTC_KINETIC"
    )
    assert a_650["divergence_score"] > 0.20
    assert a_650["quantitative_metrics"]["ntc_active_window"] is True

    # 4. NTC upper boundary 800 K: LTC active
    res_800 = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"fuel": "n-heptane", "temperature_k": 800.0, "gravity_level_g": 1e-6},
    )
    assert res_800.status_code == 200
    a_800 = next(
        a
        for a in res_800.json()["anomalies"]
        if a["anomaly_id"] == "ANOMALY_NTC_KINETIC"
    )
    assert a_800["divergence_score"] > 0.20
    assert a_800["quantitative_metrics"]["ntc_active_window"] is True


def test_tier2_anomaly_gravity_boundaries_terrestrial_vs_hypogravity(
    client: TestClient,
):
    """Tier 2: Normal gravity 1g (zero divergence) vs hypogravity 0.05g (scaled divergence)."""
    # Terrestrial 1g
    res_1g = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={
            "fuel": "n-heptane",
            "gravity_level_g": 1.0,
            "ventilation_velocity_cm_s": 3.0,
        },
    )
    assert res_1g.status_code == 200
    assert res_1g.json()["detected_anomalies_count"] == 0
    assert res_1g.json()["overall_divergence_score"] == 0.0

    # Lunar/Martian partial gravity 0.05g
    res_hypo = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={
            "fuel": "n-heptane",
            "gravity_level_g": 0.05,
            "ventilation_velocity_cm_s": 3.2,
        },
    )
    assert res_hypo.status_code == 200
    data_hypo = res_hypo.json()
    assert data_hypo["detected_anomalies_count"] >= 1
    assert 0.40 <= data_hypo["overall_divergence_score"] <= 0.65


def test_tier2_anomaly_non_sooting_and_subcritical_droplets(client: TestClient):
    """Tier 2: Methanol (non-sooting) and subcritical droplets (<1.45 mm) produce 0 divergence."""
    # Methanol (clean burning, no soot shell)
    res_methanol = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"fuel": "methanol", "initial_diameter_mm": 3.0, "gravity_level_g": 1e-6},
    )
    assert res_methanol.status_code == 200
    a_meth = next(
        a
        for a in res_methanol.json()["anomalies"]
        if a["anomaly_id"] == "ANOMALY_SOOT_SHELL_TRAPPING"
    )
    assert a_meth["divergence_score"] == 0.0
    assert a_meth["quantitative_metrics"]["trapped_energy_sustains_cool_flame"] is False

    # Subcritical heptane droplet (1.0 mm < 1.45 mm critical diameter)
    res_subcrit = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"fuel": "n-heptane", "initial_diameter_mm": 1.0, "gravity_level_g": 1e-6},
    )
    assert res_subcrit.status_code == 200
    a_sub = next(
        a
        for a in res_subcrit.json()["anomalies"]
        if a["anomaly_id"] == "ANOMALY_SOOT_SHELL_TRAPPING"
    )
    assert a_sub["divergence_score"] == 0.0


def test_tier2_anomaly_payload_validation_errors(client: TestClient):
    """Tier 2: Pydantic schema validation boundary rejects unphysical inputs with HTTP 422."""
    # Negative ventilation velocity
    res_neg_u = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"ventilation_velocity_cm_s": -2.5},
    )
    assert res_neg_u.status_code == 422

    # Excessive O2 percentage (>100%)
    res_high_o2 = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"ambient_o2_percentage": 110.0},
    )
    assert res_high_o2.status_code == 422

    # Temperature below 100 K
    res_sub_zero = client.post(
        "/api/v1/kinetics/anomalies/detect",
        json={"fuel_temperature_k": 40.0},
    )
    assert res_sub_zero.status_code == 422


# ==============================================================================
# Tier 2 — Boundary & Corner Cases: Domain B (Suppression Simulator)
# ==============================================================================


def test_tier2_suppression_standby_no_emergency_actions(client: TestClient):
    """Tier 2: Standby mode with no emergency actions active yields uncontained combustion."""
    payload = {
        "fuel": "n-heptane",
        "initial_fuel_temperature_k": 720.0,
        "damper_isolated": False,
        "chemical_agent_released": False,
        "n2_flooding_active": False,
        "simulation_duration_s": 30.0,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["actions_applied"] == ["NO_ACTION"]
    assert data["extinction_achieved"] is False
    assert data["transient_extinction_time_s"] is None
    assert data["safe_to_restart_ventilation"] is False
    assert data["rekindle_risk_level"] == "CRITICAL_REKINDLE_HAZARD"
    assert data["residual_radical_heat_release_w"] == 65.0
    assert "Unmitigated combustion active" in data["safety_advisory"]
    assert "NO_ACTION_ACTIVE_FIRE" in data["audit_message"]


def test_tier2_suppression_damper_insufficient_duration(client: TestClient):
    """Tier 2: Damper isolation simulation duration shorter than 14.5s extinction time."""
    payload = {
        "fuel": "n-heptane",
        "initial_fuel_temperature_k": 720.0,
        "damper_isolated": True,
        "chemical_agent_released": False,
        "n2_flooding_active": False,
        "simulation_duration_s": 10.0,  # 10s < 14.5s
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["extinction_achieved"] is False
    assert data["transient_extinction_time_s"] is None
    assert "forced airflow shutdown in progress" in data["audit_message"].lower()


def test_tier2_suppression_hypobaric_vs_hyperbaric_pressures(client: TestClient):
    """Tier 2: Hypobaric exploration pressure (50 kPa) vs hyperbaric airlock pressure (150 kPa)."""
    for pressure in [50.0, 150.0]:
        payload = {
            "fuel": "n-heptane",
            "chamber_pressure_kpa": pressure,
            "damper_isolated": True,
            "chemical_agent_released": True,
            "simulation_duration_s": 20.0,
        }
        res = client.post("/api/v1/safety/suppression/simulate", json=payload)
        assert res.status_code == 200, res.text
        assert res.json()["extinction_achieved"] is True


def test_tier2_suppression_oxygen_depletion_boundaries(client: TestClient):
    """Tier 2: O2 depletion boundary conditions (near-MOC 12.0% vs hyperoxic 34.0%)."""
    # Near MOC initial oxygen
    res_low_o2 = client.post(
        "/api/v1/safety/suppression/simulate",
        json={
            "fuel": "n-heptane",
            "initial_o2_percentage": 12.0,
            "damper_isolated": True,
        },
    )
    assert res_low_o2.status_code == 200
    assert res_low_o2.json()["initial_o2_percentage"] == 12.0

    # Hyperoxic exploration atmosphere (34% O2)
    res_high_o2 = client.post(
        "/api/v1/safety/suppression/simulate",
        json={
            "fuel": "n-heptane",
            "initial_o2_percentage": 34.0,
            "damper_isolated": True,
            "chemical_agent_released": True,
        },
    )
    assert res_high_o2.status_code == 200
    assert res_high_o2.json()["initial_o2_percentage"] == 34.0
    assert res_high_o2.json()["extinction_achieved"] is True


def test_tier2_suppression_solid_materials_bass2_pmma_nomex(client: TestClient):
    """Tier 2: Spacecraft solid materials (BASS-II PMMA with LOI=17.5%, and Nomex)."""
    # PMMA
    res_pmma = client.post(
        "/api/v1/safety/suppression/simulate",
        json={
            "fuel": "pmma",
            "n2_flooding_active": True,
            "n2_target_o2_percentage": 9.5,
        },
    )
    assert res_pmma.status_code == 200
    data_pmma = res_pmma.json()
    assert data_pmma["fuel_formula"] == "(C5O2H8)n"
    assert data_pmma["extinction_achieved"] is True
    assert data_pmma["transient_extinction_time_s"] < 7.0

    # Nomex
    res_nomex = client.post(
        "/api/v1/safety/suppression/simulate",
        json={
            "fuel": "nomex",
            "damper_isolated": True,
            "chemical_agent_released": True,
        },
    )
    assert res_nomex.status_code == 200
    assert res_nomex.json()["extinction_achieved"] is True


def test_tier2_suppression_payload_validation_errors(client: TestClient):
    """Tier 2: Schema validation rejects invalid temperature, O2 percentage, and unsupported fuel."""
    # Temperature below 100 K
    res_t = client.post(
        "/api/v1/safety/suppression/simulate", json={"initial_fuel_temperature_k": 50.0}
    )
    assert res_t.status_code == 422

    # Oxygen percentage above 100%
    res_o2 = client.post(
        "/api/v1/safety/suppression/simulate", json={"initial_o2_percentage": 110.0}
    )
    assert res_o2.status_code == 422

    # Unsupported fuel identifier
    res_fuel = client.post(
        "/api/v1/safety/suppression/simulate", json={"fuel": "unsupported_alien_plasma"}
    )
    assert res_fuel.status_code == 422
    assert "Unsupported fuel or material" in res_fuel.json()["detail"]


# ==============================================================================
# Tier 3 — Cross-Feature Interactions & Action Combinations
# ==============================================================================


def test_tier3_combined_damper_and_fk5112_chemical_release(client: TestClient):
    """Tier 3: Damper Isolation + FK-5-1-12 release synergy.

    Convective shutdown stops air replenishment while chemical agent rapidly scavenges
    radicals (1.1s snap-out vs 14.5s radiative extinction).
    """
    payload = {
        "fuel": "n-heptane",
        "damper_isolated": True,
        "chemical_agent_released": True,
        "chemical_agent_type": "FK-5-1-12",
        "simulation_duration_s": 30.0,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert set(data["actions_applied"]) == {
        "DAMPER_ISOLATION",
        "CHEMICAL_AGENT_RELEASE",
    }
    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] == 1.1
    assert data["residual_radical_heat_release_w"] == 0.0
    assert data["final_ventilation_velocity_cm_s"] == 0.01
    assert data["rekindle_risk_level"] == "INERT"
    assert data["safe_to_restart_ventilation"] is True


def test_tier3_combined_damper_and_n2_flooding(client: TestClient):
    """Tier 3: Damper Isolation + N2 Flooding synergy.

    Damper cutoff accelerates chamber nitrogen dilution to MOC (extinction in 5.2s vs 7.2s).
    """
    payload = {
        "fuel": "n-heptane",
        "damper_isolated": True,
        "n2_flooding_active": True,
        "n2_target_o2_percentage": 9.5,
        "simulation_duration_s": 30.0,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert set(data["actions_applied"]) == {"DAMPER_ISOLATION", "N2_FLOODING"}
    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] == 5.2
    assert data["final_ventilation_velocity_cm_s"] == 0.01
    assert data["final_o2_percentage"] <= 10.0


def test_tier3_multimodal_suppression_damper_agent_and_n2(client: TestClient):
    """Tier 3: Maximum emergency response: Damper Isolation + Agent Release + N2 Flood."""
    payload = {
        "fuel": "n-heptane",
        "damper_isolated": True,
        "chemical_agent_released": True,
        "chemical_agent_type": "FK-5-1-12",
        "n2_flooding_active": True,
        "n2_target_o2_percentage": 9.5,
        "simulation_duration_s": 30.0,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert set(data["actions_applied"]) == {
        "DAMPER_ISOLATION",
        "CHEMICAL_AGENT_RELEASE",
        "N2_FLOODING",
    }
    assert data["extinction_achieved"] is True
    # Fastest possible extinction: 0.8s
    assert data["transient_extinction_time_s"] == 0.8
    assert data["residual_radical_heat_release_w"] == 0.0
    assert data["rekindle_risk_level"] == "INERT"
    assert data["safe_to_restart_ventilation"] is True


def test_tier3_chemical_agent_release_without_damper_isolation(client: TestClient):
    """Tier 3: Advection competition: chemical agent release with active cabin airflow.

    Ongoing draft (u = 5.0 cm/s) slightly increases extinction time to 1.5s vs 1.1s under damper isolation.
    """
    payload = {
        "fuel": "n-heptane",
        "initial_ventilation_velocity_cm_s": 5.0,
        "damper_isolated": False,
        "chemical_agent_released": True,
        "chemical_agent_type": "FK-5-1-12",
        "simulation_duration_s": 20.0,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["actions_applied"] == ["CHEMICAL_AGENT_RELEASE"]
    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] == 1.5
    assert data["final_ventilation_velocity_cm_s"] == 5.0
    assert data["rekindle_risk_level"] == "INERT"


def test_tier3_rekindle_hazard_upon_ventilation_restart_after_damper_isolation(
    client: TestClient,
):
    """Tier 3: Silent cool-flame rekindle hazard upon ventilation restart after damper isolation.

    Damper isolation radiatively extinguishes the visible flame, but residence time surge
    maintains cool-flame radicals. Restarting ventilation before fuel cools triggers rekindling.
    """
    payload = {
        "fuel": "n-heptane",
        "initial_fuel_temperature_k": 720.0,
        "damper_isolated": True,
        "chemical_agent_released": False,
        "n2_flooding_active": False,
        "simulation_duration_s": 30.0,
        "restart_ventilation_velocity_cm_s": 3.0,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["extinction_achieved"] is True
    # Fuel temperature remains near NTC plateau (~705 K)
    assert data["final_temperature_k"] > 600.0
    assert data["residual_radical_heat_release_w"] > 0.0
    assert data["rekindle_probability_restart"] > 0.20
    assert data["rekindle_risk_level"] in (
        "REKINDLE_WARNING",
        "CRITICAL_REKINDLE_HAZARD",
    )
    assert data["safe_to_restart_ventilation"] is False


def test_tier3_anomaly_to_suppression_workflow_integration(client: TestClient):
    """Tier 3: Cross-system workflow coupling Anomaly Detection telemetry to Suppression Simulation.

    1. Detection of Low-Speed Micro-Draft Paradox at 3.0 cm/s
    2. Feed telemetry to Cabin Suppression Simulator to evaluate damper isolation
    3. Confirm damper isolation neutralizes micro-draft acceleration
    """
    # Step 1: Detect micro-draft anomaly
    detect_req = {
        "fuel": "pmma",
        "regime": "solid_flame_spread",
        "ventilation_velocity_cm_s": 3.0,
        "gravity_level_g": 1e-6,
    }
    detect_res = client.post("/api/v1/kinetics/anomalies/detect", json=detect_req)
    assert detect_res.status_code == 200
    detect_data = detect_res.json()
    assert detect_data["detected_anomalies_count"] >= 1
    top_anomaly = detect_data["anomalies_detected"][0]
    assert top_anomaly["anomaly_id"] == "ANOMALY_MICRO_DRAFT_PARADOX"

    # Step 2: Feed into suppression engine to isolate ventilation damper
    suppress_req = {
        "fuel": "pmma",
        "initial_ventilation_velocity_cm_s": top_anomaly["quantitative_metrics"][
            "ventilation_velocity_cm_s"
        ],
        "damper_isolated": True,
        "simulation_duration_s": 30.0,
    }
    suppress_res = client.post("/api/v1/safety/suppression/simulate", json=suppress_req)
    assert suppress_res.status_code == 200
    suppress_data = suppress_res.json()
    assert suppress_data["final_ventilation_velocity_cm_s"] == 0.01
    assert suppress_data["extinction_achieved"] is True


# ==============================================================================
# Tier 4 — Real-World Application Scenarios (from TEST_INFRA.md)
# ==============================================================================


def test_tier4_scenario_1_iss_msg_bass_ii_micro_draft_flareup(client: TestClient):
    """Tier 4 - Scenario 1: ISS MSG BASS-II Micro-Draft Flare-up (MSG Small Flow Duct).

    Exercises: F1 (Micro-Draft Paradox), F4 (NTRS Citations), F5 (Anomaly API), F6 (Damper Isolation).
    In the MSG Small Flow Duct, a 3.0 cm/s concurrent draft accelerates solid PMMA flame spread up to ~2.8x.
    The anomaly is identified with authentic BASS-II citation 20210011385, and damper isolation is simulated.
    """
    # 1. Microgravity Science Glovebox telemetry analysis
    msg_telemetry = {
        "fuel": "pmma",
        "regime": "solid_flame_spread",
        "ventilation_velocity_cm_s": 3.0,
        "ambient_o2_percentage": 21.0,
        "gravity_level_g": 1e-6,
        "chamber_pressure_kpa": 101.3,
    }
    res_detect = client.post("/api/v1/kinetics/anomalies/detect", json=msg_telemetry)
    assert res_detect.status_code == 200, res_detect.text
    data_detect = res_detect.json()

    # Contradiction verification
    paradox = next(
        a
        for a in data_detect["anomalies_detected"]
        if a["anomaly_id"] == "ANOMALY_MICRO_DRAFT_PARADOX"
    )
    assert paradox["divergence_score"] >= 0.90
    assert paradox["quantitative_metrics"]["flame_spread_acceleration_factor"] > 2.0
    assert paradox["citations"][0]["ntrs_id"] == "20210011385"

    # 2. Flight controller responds by isolating MSG ventilation damper
    res_suppress = client.post(
        "/api/v1/safety/suppression/simulate",
        json={
            "fuel": "pmma",
            "initial_ventilation_velocity_cm_s": 3.0,
            "damper_isolated": True,
        },
    )
    assert res_suppress.status_code == 200, res_suppress.text
    data_suppress = res_suppress.json()
    assert data_suppress["final_ventilation_velocity_cm_s"] == 0.01
    assert data_suppress["extinction_achieved"] is True


def test_tier4_scenario_2_cir_droplet_radiative_quench_cool_flame_survival(
    client: TestClient,
):
    """Tier 4 - Scenario 2: CIR Droplet Radiative Quench & Cool-Flame Survival (CIR / MDCA Chamber).

    Exercises: F2 (Soot-Shell Trapping), F3 (NTC Kinetic Anomaly), F4 (NTRS Citations), F5 (Anomaly API).
    In the CIR chamber, a 3.0 mm n-heptane droplet forms a soot shell radiatively quenching
    the hot flame at d_ext ≈ 0.68 d0 while trapping heat. In microgravity, peroxy radical chemistry
    with Da_cool >= 1.0 sustains cool-flame survival at 720 K.
    """
    cir_telemetry = {
        "fuel": "n-heptane",
        "droplet_diameter_mm": 3.0,
        "temperature_k": 720.0,
        "gravity_level": "microgravity (~10^-6 g)",
        "chamber_pressure_kpa": 101.325,
    }
    response = client.post("/api/v1/kinetics/anomalies/detect", json=cir_telemetry)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["detected_anomalies_count"] >= 2

    # Verify Anomaly 2: Soot Shell Radiative Trapping (FLEX)
    soot_anomaly = next(
        a for a in data["anomalies"] if a["anomaly_id"] == "ANOMALY_SOOT_SHELL_TRAPPING"
    )
    assert soot_anomaly["quantitative_metrics"]["extinction_diameter_ratio"] >= 0.60
    assert (
        soot_anomaly["quantitative_metrics"]["trapped_energy_sustains_cool_flame"]
        is True
    )
    assert any(c["ntrs_id"] == "20150023456" for c in soot_anomaly["citations"])

    # Verify Anomaly 3: NTC Kinetic Anomaly (ACME)
    ntc_anomaly = next(
        a for a in data["anomalies"] if a["anomaly_id"] == "ANOMALY_NTC_KINETIC"
    )
    assert ntc_anomaly["quantitative_metrics"]["damkohler_cool"] >= 1.0
    assert ntc_anomaly["quantitative_metrics"]["stable_cool_flame_possible"] is True
    assert any(c["ntrs_id"] == "20190001859" for c in ntc_anomaly["citations"])


def test_tier4_scenario_3_flight_controller_emergency_damper_rekindle_hazard(
    client: TestClient,
):
    """Tier 4 - Scenario 3: Flight Controller Emergency Damper Isolation + Rekindle Hazard (Cabin Ventilation System).

    Exercises: F6 (Damper Isolation), F9 (Transient Extinction & Rekindling), F10 (Suppression API).
    Flight controller isolates ventilation dampers on n-heptane fire. Flame extinguishes radiatively
    at 14.5s. When evaluating post-incident ventilation restart, the system detects high rekindling
    probability and triggers flight warning preventing premature restart.
    """
    payload = {
        "fuel": "n-heptane",
        "initial_fuel_temperature_k": 720.0,
        "initial_ventilation_velocity_cm_s": 3.0,
        "damper_isolated": True,
        "chemical_agent_released": False,
        "n2_flooding_active": False,
        "simulation_duration_s": 30.0,
        "restart_ventilation_velocity_cm_s": 3.0,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] == 14.5
    assert data["residual_radical_heat_release_w"] > 0.0
    assert data["safe_to_restart_ventilation"] is False
    assert data["rekindle_risk_level"] in (
        "REKINDLE_WARNING",
        "CRITICAL_REKINDLE_HAZARD",
    )
    assert "DO NOT restart ventilation until fuel cools" in data["safety_advisory"]
    assert "DAMPER_ISOLATION_STANDBY" in data["audit_message"]


def test_tier4_scenario_4_clean_agent_fk5112_radical_scavenging_snapout(
    client: TestClient,
):
    """Tier 4 - Scenario 4: Clean Agent FK-5-1-12 Radical Scavenging Snap-Out (Avionics / Crew Cabin).

    Exercises: F7 (FK-5-1-12 Chemical Release), F9 (Extinction Dynamics), F10 (Suppression API).
    In an avionics compartment, FK-5-1-12 discharges, catalytically scavenging radicals and
    endothermically dropping core temperature below flash point within 1.1s, ensuring permanent inert status.
    """
    payload = {
        "fuel": "n-heptane",
        "initial_fuel_temperature_k": 720.0,
        "damper_isolated": True,
        "chemical_agent_released": True,
        "chemical_agent_type": "FK-5-1-12",
        "simulation_duration_s": 25.0,
        "time_step_s": 0.5,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] == 1.1
    assert data["residual_radical_heat_release_w"] == 0.0
    assert data["final_temperature_k"] <= 315.0
    assert data["rekindle_probability_restart"] == 0.0
    assert data["rekindle_risk_level"] == "INERT"
    assert data["safe_to_restart_ventilation"] is True
    assert "SUPPRESSION_SUCCESS" in data["audit_message"]

    # Verify agent reaches design concentration
    last_point = data["decay_curve"][-1]
    assert last_point["agent_concentration_vol_pct"] >= 5.7


def test_tier4_scenario_5_multimodal_emergency_response_artemis_gateway(
    client: TestClient,
):
    """Tier 4 - Scenario 5: Multimodal Emergency Response: Damper + FK + N2 Flood (Artemis Gateway Habitat).

    Exercises: F6 (Damper Isolation), F7 (Chemical Release), F8 (N2 Flooding), F9 (Extinction Dynamics), F10 (API).
    In the Artemis Gateway habitat exploration atmosphere (34% O2, 56.5 kPa), an emergency fire alarm triggers
    the full triple-redundant mitigation matrix: damper isolation, clean agent injection, and nitrogen flooding.
    Achieves ultra-fast extinction in 0.8s and complete system inerting.
    """
    gateway_payload = {
        "fuel": "n-heptane",
        "initial_o2_percentage": 34.0,
        "chamber_pressure_kpa": 56.5,
        "initial_fuel_temperature_k": 720.0,
        "damper_isolated": True,
        "chemical_agent_released": True,
        "chemical_agent_type": "FK-5-1-12",
        "n2_flooding_active": True,
        "n2_target_o2_percentage": 9.5,
        "simulation_duration_s": 30.0,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=gateway_payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert set(data["actions_applied"]) == {
        "DAMPER_ISOLATION",
        "CHEMICAL_AGENT_RELEASE",
        "N2_FLOODING",
    }
    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] == 0.8
    assert data["initial_o2_percentage"] == 34.0
    assert data["final_o2_percentage"] <= 10.0
    assert data["residual_radical_heat_release_w"] == 0.0
    assert data["rekindle_risk_level"] == "INERT"
    assert data["safe_to_restart_ventilation"] is True
    assert "SUPPRESSION_SUCCESS" in data["audit_message"]
