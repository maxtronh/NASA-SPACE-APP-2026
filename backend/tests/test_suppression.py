"""Comprehensive unit and integration test suite for E-12 Cabin Fire Suppression & Damper Simulator."""

import pytest
from backend.app.main import app
from backend.app.safety.standards import SPACECRAFT_MATERIALS
from backend.app.safety.suppression import (
    AGENT_DESIGN_CONC_VOL_PCT,
    CabinSuppressionEngine,
)
from backend.app.schemas.suppression import (
    CabinSuppressionRequest,
    CabinSuppressionResponse,
)
from fastapi.testclient import TestClient

# --- 1. Fuel and Material Catalog Resolution ---

def test_resolve_standard_alkane_fuels():
    """Validates resolution of authoritative LTC alkane fuels and their parameters."""
    for fuel_name in ["n-heptane", "n-octane", "n-decane"]:
        props = CabinSuppressionEngine.resolve_fuel_or_material(fuel_name)
        assert props["supports_ltc"] is True
        assert props["flash_point_k"] > 0.0
        assert props["e_ltc_j_mol"] is not None
        assert props["a_ltc_s_inv"] is not None
        assert props["is_solid_material"] is False


def test_resolve_fuel_aliases():
    """Validates resolution of common chemical aliases for fuel identifiers."""
    aliases = [
        ("heptane", "n-Heptane"),
        ("c7h16", "n-Heptane"),
        ("octane", "n-Octane"),
        ("c8h18", "n-Octane"),
        ("decane", "n-Decane"),
        ("c10h22", "n-Decane"),
    ]
    for alias, expected_name in aliases:
        props = CabinSuppressionEngine.resolve_fuel_or_material(alias)
        assert props["name"] == expected_name


def test_resolve_non_ltc_fuels():
    """Validates resolution of non-LTC fuels like methanol, ethanol, methane."""
    for fuel_name in ["methanol", "ethanol", "methane"]:
        props = CabinSuppressionEngine.resolve_fuel_or_material(fuel_name)
        assert props["supports_ltc"] is False
        assert props["e_ltc_j_mol"] is None


def test_resolve_spacecraft_solid_materials():
    """Validates resolution of NASA-STD-6001B solid spacecraft materials (BASS-II PMMA, Nomex, etc.)."""
    for mat_key, expected_profile in SPACECRAFT_MATERIALS.items():
        props = CabinSuppressionEngine.resolve_fuel_or_material(mat_key)
        assert props["name"] == expected_profile.name
        assert props["formula"] == expected_profile.chemical_formula
        assert props["limiting_oxygen_index"] == expected_profile.limiting_oxygen_index
        assert props["is_solid_material"] is True


def test_resolve_unsupported_fuel_raises_error():
    """Ensures unrecognized fuel identifiers raise ValueError with helpful error message."""
    with pytest.raises(ValueError, match="Unsupported fuel or material 'unobtanium'"):
        CabinSuppressionEngine.resolve_fuel_or_material("unobtanium")


# --- 2. Baseline Scenario: No Emergency Suppression Action ---

def test_suppression_baseline_no_action():
    """Tests baseline state when no emergency response action is initiated."""
    req = CabinSuppressionRequest(
        fuel="n-heptane",
        initial_fuel_temperature_k=720.0,
        initial_o2_percentage=21.0,
        initial_ventilation_velocity_cm_s=3.0,
        damper_isolated=False,
        chemical_agent_released=False,
        n2_flooding_active=False,
        simulation_duration_s=30.0,
        time_step_s=1.0,
    )
    res = CabinSuppressionEngine.simulate(req)

    assert isinstance(res, CabinSuppressionResponse)
    assert res.actions_applied == ["NO_ACTION"]
    assert res.extinction_achieved is False
    assert res.transient_extinction_time_s is None
    assert res.safe_to_restart_ventilation is False
    assert res.rekindle_risk_level == "CRITICAL_REKINDLE_HAZARD"
    assert res.final_temperature_k >= 700.0
    assert res.residual_radical_heat_release_w == 65.0
    assert "Unmitigated combustion active" in res.safety_advisory
    assert "NO_ACTION_ACTIVE_FIRE" in res.audit_message
    assert len(res.decay_curve) == 31


# --- 3. Emergency Action A: Damper Isolation ---

def test_suppression_damper_isolation_microgravity_extinction():
    """Tests damper isolation shutting off forced airflow with radiative hot-flame extinction."""
    req = CabinSuppressionRequest(
        fuel="n-heptane",
        initial_fuel_temperature_k=720.0,
        initial_o2_percentage=21.0,
        initial_ventilation_velocity_cm_s=3.0,
        damper_isolated=True,
        chemical_agent_released=False,
        n2_flooding_active=False,
        simulation_duration_s=30.0,
        time_step_s=0.5,
        restart_ventilation_velocity_cm_s=3.0,
    )
    res = CabinSuppressionEngine.simulate(req)

    assert res.actions_applied == ["DAMPER_ISOLATION"]
    assert res.extinction_achieved is True
    assert res.transient_extinction_time_s == 14.5
    # Airflow reduced to microgravity molecular diffusion floor
    assert res.final_ventilation_velocity_cm_s == 0.01

    # Cool flame / radical persistence: residence time surged, fuel still above flash point
    assert res.final_temperature_k > 269.15  # n-heptane flash point
    assert res.residual_radical_heat_release_w > 0.0

    # Rekindling trap: re-starting ventilation with hot fuel triggers rekindle warning
    assert res.rekindle_probability_restart > 0.20
    assert res.rekindle_risk_level in ["REKINDLE_WARNING", "CRITICAL_REKINDLE_HAZARD"]
    assert res.safe_to_restart_ventilation is False
    assert "DO NOT restart ventilation" in res.safety_advisory
    assert "DAMPER_ISOLATION_STANDBY" in res.audit_message


def test_suppression_damper_isolation_short_duration_no_extinction():
    """If simulation duration is shorter than radiative extinction time, extinction is not achieved."""
    req = CabinSuppressionRequest(
        fuel="n-heptane",
        initial_fuel_temperature_k=720.0,
        damper_isolated=True,
        simulation_duration_s=10.0,  # 10s < 14.5s
        time_step_s=1.0,
    )
    res = CabinSuppressionEngine.simulate(req)
    assert res.extinction_achieved is False
    assert res.transient_extinction_time_s is None


# --- 4. Emergency Action B: Chemical Agent Release ---

def test_suppression_fk5112_chemical_agent_rapid_quench():
    """Tests FK-5-1-12 clean agent rapid catalytic radical scavenging and endothermic quench."""
    req = CabinSuppressionRequest(
        fuel="n-heptane",
        initial_fuel_temperature_k=720.0,
        initial_o2_percentage=21.0,
        initial_ventilation_velocity_cm_s=3.0,
        damper_isolated=False,
        chemical_agent_released=True,
        chemical_agent_type="FK-5-1-12",
        n2_flooding_active=False,
        simulation_duration_s=30.0,
        time_step_s=0.5,
    )
    res = CabinSuppressionEngine.simulate(req)

    assert res.actions_applied == ["CHEMICAL_AGENT_RELEASE"]
    assert res.extinction_achieved is True
    assert 1.0 <= res.transient_extinction_time_s <= 2.0
    # Radical heat release annihilated
    assert res.residual_radical_heat_release_w == 0.0
    # Thermal quench down to ambient
    assert res.final_temperature_k <= 315.0

    # Permanent inert: zero rekindling hazard
    assert res.rekindle_probability_restart == 0.0
    assert res.damkohler_cool_restart == 0.0
    assert res.rekindle_risk_level == "INERT"
    assert res.safe_to_restart_ventilation is True
    assert "Safe to restore ventilation" in res.safety_advisory
    assert "SUPPRESSION_SUCCESS" in res.audit_message

    # Verify agent concentration in decay curve
    final_decay = res.decay_curve[-1]
    assert final_decay.agent_concentration_vol_pct == AGENT_DESIGN_CONC_VOL_PCT


def test_suppression_halon_1301_chemical_agent():
    """Tests Halon 1301 agent discharge with catalytic radical scavenging."""
    req = CabinSuppressionRequest(
        fuel="n-octane",
        initial_fuel_temperature_k=750.0,
        chemical_agent_released=True,
        chemical_agent_type="Halon 1301",
        simulation_duration_s=20.0,
        time_step_s=0.5,
    )
    res = CabinSuppressionEngine.simulate(req)

    assert res.extinction_achieved is True
    assert res.transient_extinction_time_s == 1.5
    assert res.rekindle_risk_level == "INERT"
    assert res.residual_radical_heat_release_w == 0.0
    assert res.safe_to_restart_ventilation is True
    assert "Halon 1301 successfully scavenged" in res.safety_advisory


# --- 5. Emergency Action C: Nitrogen (N2) Flooding ---

def test_suppression_n2_flooding_dilution_extinction():
    """Tests hypobaric N2 dilution lowering cabin O2 below MOC."""
    req = CabinSuppressionRequest(
        fuel="n-heptane",
        initial_fuel_temperature_k=720.0,
        initial_o2_percentage=21.0,
        damper_isolated=False,
        chemical_agent_released=False,
        n2_flooding_active=True,
        n2_target_o2_percentage=9.5,
        simulation_duration_s=30.0,
        time_step_s=0.5,
    )
    res = CabinSuppressionEngine.simulate(req)

    assert res.actions_applied == ["N2_FLOODING"]
    assert res.extinction_achieved is True
    # Extinction occurs when O2 drops below MOC (~11.8%)
    assert 6.0 <= res.transient_extinction_time_s <= 8.5
    assert res.final_o2_percentage <= 10.0

    # N2 flood extinguishes flame but fuel cools slowly, leaving restart vulnerability
    assert "N2_FLOODING_EXTINCTION" in res.audit_message
    assert "Maintain inert N2 blanket" in res.safety_advisory


def test_suppression_n2_flooding_pmma_solid_material():
    """Tests N2 flooding against PMMA solid material (LOI = 17.5%) from BASS-II flight archives."""
    req = CabinSuppressionRequest(
        fuel="pmma",
        initial_fuel_temperature_k=650.0,
        initial_o2_percentage=21.0,
        n2_flooding_active=True,
        n2_target_o2_percentage=9.5,
        simulation_duration_s=30.0,
    )
    res = CabinSuppressionEngine.simulate(req)

    assert res.fuel_formula == "(C5O2H8)n"
    assert res.extinction_achieved is True
    # PMMA LOI is 17.5%, so extinction occurs faster than alkane MOC (11.8%)
    assert res.transient_extinction_time_s is not None
    assert res.transient_extinction_time_s < 7.0


# --- 6. Combined Protocols ---

def test_suppression_combined_damper_and_chemical_agent():
    """Tests standard flight emergency combo: ventilation damper cutoff + chemical discharge."""
    req = CabinSuppressionRequest(
        fuel="n-heptane",
        damper_isolated=True,
        chemical_agent_released=True,
        chemical_agent_type="FK-5-1-12",
        n2_flooding_active=False,
        simulation_duration_s=30.0,
        time_step_s=0.5,
    )
    res = CabinSuppressionEngine.simulate(req)

    assert set(res.actions_applied) == {"DAMPER_ISOLATION", "CHEMICAL_AGENT_RELEASE"}
    assert res.extinction_achieved is True
    assert res.transient_extinction_time_s == 1.1
    assert res.residual_radical_heat_release_w == 0.0
    assert res.rekindle_risk_level == "INERT"
    assert res.safe_to_restart_ventilation is True


def test_suppression_combined_damper_and_n2_flooding():
    """Tests damper isolation combined with N2 flooding (no forced fresh draft)."""
    req = CabinSuppressionRequest(
        fuel="n-heptane",
        damper_isolated=True,
        chemical_agent_released=False,
        n2_flooding_active=True,
        n2_target_o2_percentage=9.5,
        simulation_duration_s=30.0,
    )
    res = CabinSuppressionEngine.simulate(req)

    assert set(res.actions_applied) == {"DAMPER_ISOLATION", "N2_FLOODING"}
    assert res.extinction_achieved is True
    assert res.transient_extinction_time_s == 5.2


def test_suppression_all_three_actions_applied():
    """Tests maximum spacecraft emergency protocol: Damper Isolation + Agent Release + N2 Flood."""
    req = CabinSuppressionRequest(
        fuel="n-heptane",
        damper_isolated=True,
        chemical_agent_released=True,
        n2_flooding_active=True,
        simulation_duration_s=30.0,
    )
    res = CabinSuppressionEngine.simulate(req)

    assert set(res.actions_applied) == {"DAMPER_ISOLATION", "CHEMICAL_AGENT_RELEASE", "N2_FLOODING"}
    assert res.extinction_achieved is True
    assert res.transient_extinction_time_s == 0.8
    assert res.rekindle_risk_level == "INERT"
    assert res.safe_to_restart_ventilation is True


# --- 7. Gateway High-O2 Atmosphere & Boundary Conditions ---

def test_suppression_artemis_gateway_hyperoxic_atmosphere():
    """Tests fire suppression in Artemis Gateway exploration atmosphere (34% O2, 56.5 kPa)."""
    req = CabinSuppressionRequest(
        fuel="n-heptane",
        initial_o2_percentage=34.0,
        chamber_pressure_kpa=56.5,
        damper_isolated=True,
        chemical_agent_released=True,
        simulation_duration_s=30.0,
    )
    res = CabinSuppressionEngine.simulate(req)

    assert res.initial_o2_percentage == 34.0
    assert res.extinction_achieved is True
    assert res.rekindle_risk_level == "INERT"


def test_decay_curve_fidelity_and_monotonicity():
    """Validates that suppression decay curve produces continuous, physically consistent trajectories."""
    req = CabinSuppressionRequest(
        fuel="n-heptane",
        initial_fuel_temperature_k=720.0,
        initial_ventilation_velocity_cm_s=3.0,
        damper_isolated=True,
        chemical_agent_released=True,
        simulation_duration_s=10.0,
        time_step_s=0.2,
    )
    res = CabinSuppressionEngine.simulate(req)

    curve = res.decay_curve
    assert len(curve) == 51  # 10 / 0.2 + 1
    assert curve[0].time_s == 0.0
    assert curve[-1].time_s == 10.0

    # Temperature and HRR monotonically decrease under chemical agent thermal quench
    for j in range(1, len(curve)):
        assert curve[j].temperature_k <= curve[j - 1].temperature_k + 0.1
        assert curve[j].heat_release_rate_kw <= curve[j - 1].heat_release_rate_kw + 0.01


# --- 8. API Endpoint Integration Tests ---

@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_api_simulate_suppression_endpoint_success(client):
    """Tests POST /api/v1/safety/suppression/simulate endpoint for valid emergency simulation."""
    payload = {
        "fuel": "n-heptane",
        "initial_fuel_temperature_k": 720.0,
        "initial_o2_percentage": 21.0,
        "initial_ventilation_velocity_cm_s": 3.0,
        "chamber_pressure_kpa": 101.325,
        "characteristic_length_m": 0.003,
        "damper_isolated": True,
        "chemical_agent_released": True,
        "chemical_agent_type": "FK-5-1-12",
        "n2_flooding_active": False,
        "n2_target_o2_percentage": 9.5,
        "simulation_duration_s": 30.0,
        "time_step_s": 0.5,
        "restart_ventilation_velocity_cm_s": 3.0,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["fuel"] == "n-Heptane"
    assert data["fuel_formula"] == "C7H16"
    assert "DAMPER_ISOLATION" in data["actions_applied"]
    assert "CHEMICAL_AGENT_RELEASE" in data["actions_applied"]
    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] == 1.1
    assert data["rekindle_risk_level"] == "INERT"
    assert data["safe_to_restart_ventilation"] is True
    assert data["residual_radical_heat_release_w"] == 0.0
    assert len(data["decay_curve"]) == 61


def test_api_simulate_suppression_damper_only_endpoint(client):
    """Tests POST /api/v1/safety/suppression/simulate for damper isolation warning scenario."""
    payload = {
        "fuel": "n-heptane",
        "damper_isolated": True,
        "chemical_agent_released": False,
        "n2_flooding_active": False,
    }
    response = client.post("/api/v1/safety/suppression/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["actions_applied"] == ["DAMPER_ISOLATION"]
    assert data["extinction_achieved"] is True
    assert data["transient_extinction_time_s"] == 14.5
    assert data["safe_to_restart_ventilation"] is False
    assert data["rekindle_risk_level"] in ["REKINDLE_WARNING", "CRITICAL_REKINDLE_HAZARD"]


def test_api_simulate_suppression_validation_errors(client):
    """Tests Pydantic validation error handling on invalid requests."""
    # Invalid temperature (< 100 K)
    res = client.post(
        "/api/v1/safety/suppression/simulate",
        json={"initial_fuel_temperature_k": 50.0},
    )
    assert res.status_code == 422

    # Invalid oxygen percentage (> 100%)
    res = client.post(
        "/api/v1/safety/suppression/simulate",
        json={"initial_o2_percentage": 105.0},
    )
    assert res.status_code == 422

    # Unsupported fuel name
    res = client.post(
        "/api/v1/safety/suppression/simulate",
        json={"fuel": "invalid_unknown_substance_xyz"},
    )
    assert res.status_code == 422
    assert "Unsupported fuel or material" in res.json()["detail"]
