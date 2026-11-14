"""Unit and integration tests for Silent Cool-Flame Rekindling Early Warning System (Upgrade E-11)."""

import math
import pytest
from fastapi.testclient import TestClient

from backend.app.kinetics.rekindle_warning import (
    LTC_FUEL_PROFILES,
    R_GAS_CONSTANT,
    RekindleWarningEngine,
)
from backend.app.schemas.rekindle import (
    CoolFlameStreamMonitorRequest,
    RekindleWarningRequest,
)


# --- 1. Fuel Catalog & Profile Resolution ---

def test_fuel_profile_resolution():
    """Verify fuel profile resolution for standard fuels and aliases."""
    for fuel_key in ["n-heptane", "n-octane", "n-decane"]:
        key, profile = RekindleWarningEngine.resolve_fuel_profile(fuel_key)
        assert key == fuel_key
        assert profile["supports_ltc"] is True
        assert profile["flash_point_k"] > 0
        assert profile["e_ltc_j_mol"] > 0
        assert profile["a_ltc_s_inv"] > 0

    # Aliases
    aliases = [
        ("heptane", "n-heptane"),
        ("c7h16", "n-heptane"),
        ("octane", "n-octane"),
        ("c8h18", "n-octane"),
        ("decane", "n-decane"),
        ("c10h22", "n-decane"),
        ("ch3oh", "methanol"),
        ("methyl alcohol", "methanol"),
        ("ethanol", "ethanol"),
        ("c2h5oh", "ethanol"),
        ("methane", "methane"),
    ]
    for alias, expected in aliases:
        key, profile = RekindleWarningEngine.resolve_fuel_profile(alias)
        assert key == expected

    # Unknown fuel raises ValueError
    with pytest.raises(ValueError, match="Unsupported fuel 'hydrogen'"):
        RekindleWarningEngine.resolve_fuel_profile("hydrogen")


# --- 2. Damköhler Number Physical Calibration ---

def test_damkohler_analytical_calibration():
    """Validates Damköhler number calculation against exact analytical Arrhenius values."""
    # Test conditions: n-heptane, L = 3 mm (0.003 m), U_vent = 0.05 m/s, T = 720.0 K
    L = 0.003
    U = 0.05
    T = 720.0
    da, tau_res, tau_chem = RekindleWarningEngine.calculate_damkohler_cool(
        characteristic_length_m=L,
        ventilation_velocity_m_s=U,
        fuel="n-heptane",
        temperature_k=T,
    )

    # Analytical values
    expected_tau_res = L / U  # 0.06 s
    assert pytest.approx(tau_res, rel=1e-5) == expected_tau_res

    prof = LTC_FUEL_PROFILES["n-heptane"]
    k_expected = prof["a_ltc_s_inv"] * math.exp(-prof["e_ltc_j_mol"] / (R_GAS_CONSTANT * T))
    expected_tau_chem = 1.0 / k_expected
    expected_da = expected_tau_res / expected_tau_chem

    assert pytest.approx(tau_chem, rel=1e-5) == expected_tau_chem
    assert pytest.approx(da, rel=1e-5) == expected_da
    assert 1.0 < da < 1.15  # Consistent with calibrated ~1.05


def test_damkohler_temperature_and_velocity_scaling():
    """Verify physical scaling: Da increases with T (faster reaction) and decreases with U_vent (shorter residence)."""
    # Increasing temperature
    da_650, _, _ = RekindleWarningEngine.calculate_damkohler_cool(0.003, 0.05, "n-heptane", 650.0)
    da_720, _, _ = RekindleWarningEngine.calculate_damkohler_cool(0.003, 0.05, "n-heptane", 720.0)
    da_800, _, _ = RekindleWarningEngine.calculate_damkohler_cool(0.003, 0.05, "n-heptane", 800.0)
    assert da_650 < da_720 < da_800

    # Increasing ventilation velocity
    da_u01, _, _ = RekindleWarningEngine.calculate_damkohler_cool(0.003, 0.01, "n-heptane", 720.0)
    da_u05, _, _ = RekindleWarningEngine.calculate_damkohler_cool(0.003, 0.05, "n-heptane", 720.0)
    da_u50, _, _ = RekindleWarningEngine.calculate_damkohler_cool(0.003, 0.50, "n-heptane", 720.0)
    assert da_u01 > da_u05 > da_u50


def test_damkohler_all_alkane_fuels():
    """Verify Da_cool calculation across n-octane and n-decane."""
    for fuel in ["n-octane", "n-decane"]:
        da, tau_res, tau_chem = RekindleWarningEngine.calculate_damkohler_cool(
            0.003, 0.05, fuel, 720.0
        )
        assert da > 0.0
        assert tau_res == pytest.approx(0.06, rel=1e-4)
        assert tau_chem is not None and tau_chem > 0.0


# --- 3. Flash Point Strict Boundary Enforcement ---

def test_flash_point_strict_cutoff():
    """Crucial safety invariant: if T_fuel <= T_flash, P_rekindle must be strictly 0.0."""
    # n-heptane flash point is 269.15 K (-4 °C)
    t_flash = LTC_FUEL_PROFILES["n-heptane"]["flash_point_k"]

    # Even with an artificially high Damköhler number (e.g. 5.0)
    p_below = RekindleWarningEngine.calculate_rekindle_probability(
        damkohler_cool=5.0,
        fuel_temp_k=250.0,
        flash_point_k=t_flash,
        da_crit=1.0,
        theta=0.20,
        supports_ltc=True,
    )
    assert p_below == 0.0

    # Exact boundary condition T == T_flash
    p_boundary = RekindleWarningEngine.calculate_rekindle_probability(
        damkohler_cool=5.0,
        fuel_temp_k=t_flash,
        flash_point_k=t_flash,
        da_crit=1.0,
        theta=0.20,
        supports_ltc=True,
    )
    assert p_boundary == 0.0

    # Immediately above flash point (T = T_flash + 1.0 K)
    p_above = RekindleWarningEngine.calculate_rekindle_probability(
        damkohler_cool=1.0,
        fuel_temp_k=t_flash + 1.0,
        flash_point_k=t_flash,
        da_crit=1.0,
        theta=0.20,
        supports_ltc=True,
    )
    assert p_above == pytest.approx(0.50, abs=1e-4)

    # For n-decane (flash point 319.15 K)
    t_flash_decane = LTC_FUEL_PROFILES["n-decane"]["flash_point_k"]
    p_decane_subflash = RekindleWarningEngine.calculate_rekindle_probability(
        damkohler_cool=3.0,
        fuel_temp_k=300.0,
        flash_point_k=t_flash_decane,
        da_crit=1.0,
        theta=0.20,
        supports_ltc=True,
    )
    assert p_decane_subflash == 0.0


# --- 4. Sigmoid Probability Transition Across Da_crit ---

def test_sigmoid_probability_transition():
    """Verify logistic transition around Da_crit = 1.0 with scale theta = 0.20."""
    t_flash = 269.15
    t_fuel = 720.0  # Well above flash point

    # At bifurcation Da == Da_crit -> P = 0.50
    p_crit = RekindleWarningEngine.calculate_rekindle_probability(
        damkohler_cool=1.0,
        fuel_temp_k=t_fuel,
        flash_point_k=t_flash,
        da_crit=1.0,
        theta=0.20,
    )
    assert pytest.approx(p_crit, abs=1e-4) == 0.50

    # At Da = 1.5 (Da >> Da_crit)
    # Delta = (1.5 - 1.0) / 0.20 = 2.5 -> P = 1 / (1 + exp(-2.5)) ~ 0.92414
    p_high = RekindleWarningEngine.calculate_rekindle_probability(
        damkohler_cool=1.5,
        fuel_temp_k=t_fuel,
        flash_point_k=t_flash,
        da_crit=1.0,
        theta=0.20,
    )
    assert pytest.approx(p_high, abs=1e-3) == 0.924
    assert RekindleWarningEngine.classify_risk(p_high) == "CRITICAL_REKINDLE_HAZARD"

    # At Da = 0.5 (Da << Da_crit)
    # Delta = (0.5 - 1.0) / 0.20 = -2.5 -> P = 1 / (1 + exp(2.5)) ~ 0.07585
    p_low = RekindleWarningEngine.calculate_rekindle_probability(
        damkohler_cool=0.5,
        fuel_temp_k=t_fuel,
        flash_point_k=t_flash,
        da_crit=1.0,
        theta=0.20,
    )
    assert pytest.approx(p_low, abs=1e-3) == 0.076
    assert RekindleWarningEngine.classify_risk(p_low) == "INERT"


def test_sigmoid_extreme_values_clamp():
    """Verify numerical stability without float overflow on extreme Damköhler inputs."""
    t_flash = 269.15
    t_fuel = 720.0

    p_extreme_high = RekindleWarningEngine.calculate_rekindle_probability(
        damkohler_cool=500.0,
        fuel_temp_k=t_fuel,
        flash_point_k=t_flash,
    )
    assert p_extreme_high == 1.0

    p_extreme_low = RekindleWarningEngine.calculate_rekindle_probability(
        damkohler_cool=-500.0,
        fuel_temp_k=t_fuel,
        flash_point_k=t_flash,
    )
    assert p_extreme_low == 0.0


# --- 5. Non-LTC Fuels Preclusion ---

def test_non_ltc_fuels_inert():
    """Verify alcohols and small alkanes lacking low-temperature chemistry return INERT."""
    for non_ltc in ["methanol", "ethanol", "methane"]:
        da, tau_res, tau_chem = RekindleWarningEngine.calculate_damkohler_cool(
            characteristic_length_m=0.003,
            ventilation_velocity_m_s=0.05,
            fuel=non_ltc,
            temperature_k=720.0,
        )
        assert da == 0.0
        assert tau_chem is None

        _, profile = RekindleWarningEngine.resolve_fuel_profile(non_ltc)
        p = RekindleWarningEngine.calculate_rekindle_probability(
            damkohler_cool=da,
            fuel_temp_k=720.0,
            flash_point_k=profile["flash_point_k"],
            supports_ltc=profile["supports_ltc"],
        )
        assert p == 0.0
        assert RekindleWarningEngine.classify_risk(p) == "INERT"


# --- 6. Critical Ventilation Blowout Airspeed ---

def test_critical_ventilation_blowout_velocity():
    """Verify critical blowout airspeed U_vent,crit = (L * k_LTC) / Da_crit."""
    L = 0.003
    T = 720.0
    u_crit = RekindleWarningEngine.calculate_critical_ventilation(
        characteristic_length_m=L,
        fuel="n-heptane",
        temperature_k=T,
        da_crit=1.0,
    )
    assert 0.04 < u_crit < 0.06

    # Verify that evaluating Da with U_vent = U_vent,crit exactly yields Da = Da_crit (1.0)
    da_at_crit, _, _ = RekindleWarningEngine.calculate_damkohler_cool(
        characteristic_length_m=L,
        ventilation_velocity_m_s=u_crit,
        fuel="n-heptane",
        temperature_k=T,
    )
    assert pytest.approx(da_at_crit, rel=1e-4) == 1.0

    # Non-LTC fuel critical ventilation is 0.0
    u_crit_alcohol = RekindleWarningEngine.calculate_critical_ventilation(
        characteristic_length_m=L,
        fuel="methanol",
        temperature_k=T,
    )
    assert u_crit_alcohol == 0.0


# --- 7. Input Validation & Error Handling ---

def test_invalid_physical_inputs_raise_errors():
    """Verify physical input validation guards."""
    with pytest.raises(ValueError, match="Temperature must be strictly positive"):
        RekindleWarningEngine.calculate_damkohler_cool(0.003, 0.05, "n-heptane", -10.0)

    with pytest.raises(ValueError, match="Characteristic length must be strictly positive"):
        RekindleWarningEngine.calculate_damkohler_cool(-0.003, 0.05, "n-heptane", 720.0)

    with pytest.raises(ValueError, match="Ventilation velocity must be strictly positive"):
        RekindleWarningEngine.calculate_damkohler_cool(0.003, -0.05, "n-heptane", 720.0)

    with pytest.raises(ValueError, match="Transition scale theta must be strictly positive"):
        RekindleWarningEngine.calculate_rekindle_probability(
            damkohler_cool=1.0, fuel_temp_k=720.0, flash_point_k=269.15, theta=-0.1
        )


# --- 8. Real-Time Telemetry Stream Analyzer ---

def test_stream_analyzer_hot_extinction_and_silent_cool_flame():
    """Verify stream monitor identifies radiative extinction transition and silent cool-flame persistence."""
    req = CoolFlameStreamMonitorRequest(
        test_run_id="CIR-FLEX-01",
        fuel="n-heptane",
        timestamps=[0.0, 1.0, 2.0, 3.0, 4.0],
        temperatures_k=[1800.0, 1500.0, 720.0, 715.0, 710.0],
        radiometer_mw=[20.0, 12.0, 0.4, 0.2, 0.1],
        ventilation_velocity_m_s=0.05,
        characteristic_length_m=0.003,
    )

    resp = RekindleWarningEngine.analyze_stream(req)
    assert resp.test_run_id == "CIR-FLEX-01"
    assert resp.hot_flame_extinction_detected is True
    assert resp.hot_flame_extinction_timestamp_s == 2.0
    assert resp.cool_flame_active is True
    assert len(resp.timeline_assessments) == 5

    # Point at t=2.0 s (cool flame at 720 K)
    cool_pt = resp.timeline_assessments[2]
    assert cool_pt.cool_flame_active is True
    assert cool_pt.risk_classification == "MONITOR"
    assert cool_pt.radiometer_mw == 0.4


def test_stream_analyzer_missing_radiometer_strict_null_preservation():
    """Verify strict NULL preservation when radiometer channel is omitted, relying on dT/dt."""
    req = CoolFlameStreamMonitorRequest(
        test_run_id="CIR-FLEX-OPTICAL-BLIND",
        fuel="n-heptane",
        timestamps=[0.0, 1.0, 2.0],
        temperatures_k=[1600.0, 750.0, 720.0],
        radiometer_mw=None,
        ventilation_velocity_m_s=0.05,
    )

    resp = RekindleWarningEngine.analyze_stream(req)
    assert resp.hot_flame_extinction_detected is True
    assert resp.cool_flame_active is True
    for pt in resp.timeline_assessments:
        assert pt.radiometer_mw is None


# --- 9. FastAPI REST Endpoints Integration ---

def test_api_rekindle_risk_nominal(client: TestClient):
    """Test POST /api/v1/safety/cool-flame/rekindle-risk nominal scenario."""
    payload = {
        "fuel": "n-heptane",
        "fuel_temperature_k": 720.0,
        "ventilation_velocity_m_s": 0.05,
        "characteristic_length_m": 0.003,
        "test_run_id": "TEST-FLEX-01",
    }
    resp = client.post("/api/v1/safety/cool-flame/rekindle-risk", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["test_run_id"] == "TEST-FLEX-01"
    assert data["fuel"] == "n-Heptane"
    assert data["supports_ltc"] is True
    assert data["above_flash_point"] is True
    assert data["risk_classification"] in ["MONITOR", "REKINDLE_WARNING"]
    assert data["damkohler_cool"] > 0
    assert 0.0 <= data["rekindle_probability"] <= 1.0
    assert data["critical_ventilation_velocity_m_s"] > 0
    assert "advisory_message" in data


def test_api_rekindle_risk_sub_flash_point(client: TestClient):
    """Test POST /api/v1/safety/cool-flame/rekindle-risk below flash point."""
    payload = {
        "fuel": "n-heptane",
        "fuel_temperature_k": 260.0,  # Below flash point 269.15 K
        "ventilation_velocity_m_s": 0.05,
    }
    resp = client.post("/api/v1/safety/cool-flame/rekindle-risk", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["above_flash_point"] is False
    assert data["rekindle_probability"] == 0.0
    assert data["risk_classification"] == "INERT"
    assert "below" in data["advisory_message"].lower()


def test_api_rekindle_risk_critical_hazard(client: TestClient):
    """Test POST /api/v1/safety/cool-flame/rekindle-risk high temperature critical hazard."""
    payload = {
        "fuel": "n-heptane",
        "fuel_temperature_k": 840.0,  # High peroxy rate
        "ventilation_velocity_m_s": 0.02,  # Low ventilation
    }
    resp = client.post("/api/v1/safety/cool-flame/rekindle-risk", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["risk_classification"] == "CRITICAL_REKINDLE_HAZARD"
    assert data["rekindle_probability"] >= 0.85
    assert "CRITICAL" in data["advisory_message"]


def test_api_rekindle_risk_non_ltc_fuel(client: TestClient):
    """Test POST /api/v1/safety/cool-flame/rekindle-risk with non-LTC fuel."""
    payload = {
        "fuel": "methanol",
        "fuel_temperature_k": 720.0,
    }
    resp = client.post("/api/v1/safety/cool-flame/rekindle-risk", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["supports_ltc"] is False
    assert data["rekindle_probability"] == 0.0
    assert data["risk_classification"] == "INERT"


def test_api_rekindle_risk_validation_errors(client: TestClient):
    """Test validation errors on invalid request inputs."""
    # Temperature out of bounds (< 100 K)
    resp = client.post("/api/v1/safety/cool-flame/rekindle-risk", json={"fuel_temperature_k": 50.0})
    assert resp.status_code == 422

    # Ventilation out of bounds (<= 0)
    resp = client.post("/api/v1/safety/cool-flame/rekindle-risk", json={"ventilation_velocity_m_s": 0.0})
    assert resp.status_code == 422

    # Characteristic length out of bounds (<= 0)
    resp = client.post("/api/v1/safety/cool-flame/rekindle-risk", json={"characteristic_length_m": 0.0})
    assert resp.status_code == 422

    # Unknown fuel
    resp = client.post("/api/v1/safety/cool-flame/rekindle-risk", json={"fuel": "xenon"})
    assert resp.status_code == 422


def test_api_stream_monitor_nominal(client: TestClient):
    """Test POST /api/v1/safety/cool-flame/stream-monitor nominal stream processing."""
    payload = {
        "test_run_id": "FLIGHT-TELEMETRY-09",
        "fuel": "n-heptane",
        "timestamps": [0.0, 1.0, 2.0, 3.0],
        "temperatures_k": [1700.0, 1300.0, 720.0, 710.0],
        "radiometer_mw": [18.0, 9.5, 0.8, 0.3],
        "ventilation_velocity_m_s": 0.05,
    }
    resp = client.post("/api/v1/safety/cool-flame/stream-monitor", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["test_run_id"] == "FLIGHT-TELEMETRY-09"
    assert data["hot_flame_extinction_detected"] is True
    assert data["cool_flame_active"] is True
    assert len(data["timeline_assessments"]) == 4
    assert "safety_status" in data


def test_api_stream_monitor_mismatched_lengths(client: TestClient):
    """Test POST /api/v1/safety/cool-flame/stream-monitor rejection of mismatched array lengths."""
    # Timestamps (3) vs Temperatures (2)
    payload = {
        "test_run_id": "MISMATCH-01",
        "fuel": "n-heptane",
        "timestamps": [0.0, 1.0, 2.0],
        "temperatures_k": [1500.0, 720.0],
    }
    resp = client.post("/api/v1/safety/cool-flame/stream-monitor", json=payload)
    assert resp.status_code == 422

    # Timestamps (2) vs Radiometer (3)
    payload_rad = {
        "test_run_id": "MISMATCH-02",
        "fuel": "n-heptane",
        "timestamps": [0.0, 1.0],
        "temperatures_k": [1500.0, 720.0],
        "radiometer_mw": [10.0, 5.0, 1.0],
    }
    resp_rad = client.post("/api/v1/safety/cool-flame/stream-monitor", json=payload_rad)
    assert resp_rad.status_code == 422


def test_api_stream_monitor_min_length(client: TestClient):
    """Test POST /api/v1/safety/cool-flame/stream-monitor with fewer than 2 data points."""
    payload = {
        "test_run_id": "TOO-SHORT",
        "timestamps": [0.0],
        "temperatures_k": [720.0],
    }
    resp = client.post("/api/v1/safety/cool-flame/stream-monitor", json=payload)
    assert resp.status_code == 422
