"""Unit and integration tests for Exploration Atmosphere Fire Hazard Index (EAFHI) (Upgrade E-10)."""

import pytest
from fastapi.testclient import TestClient

from backend.app.safety.eafhi import (
    CLASS_1_LIMIT,
    CLASS_2_LIMIT,
    CLASS_3_LIMIT,
    EAFHIEngine,
)
from backend.app.safety.standards import SPACECRAFT_MATERIALS


def test_gas_thermodynamics_gateway_atmosphere():
    # Artemis Lunar Gateway: P = 56.5 kPa, X_O2 = 34.0%, T = 298.15 K
    rho, mu, nu = EAFHIEngine.calculate_gas_properties(pressure_kpa=56.5, oxygen_percentage=34.0)

    # Ideal gas mixture density should be ~ 0.669 kg/m3 (vs ~1.18 kg/m3 at sea level)
    assert pytest.approx(rho, abs=0.01) == 0.669
    # Dynamic viscosity via Sutherland formula ~ 1.837e-5 Pa*s
    assert pytest.approx(mu, rel=1e-2) == 1.837e-5
    # Kinematic viscosity nu = mu / rho ~ 2.74e-5 m2/s
    assert pytest.approx(nu, rel=1e-2) == 2.74e-5


def test_grashof_number_and_buoyancy_factor():
    _, _, nu_gw = EAFHIEngine.calculate_gas_properties(pressure_kpa=56.5, oxygen_percentage=34.0)

    # Grashof in Gateway lunar gravity (g = 1.62 m/s2, L = 0.05 m, Tf = 1800 K)
    gr_gw = EAFHIEngine.calculate_grashof_number(
        gravity_ms2=1.62,
        characteristic_length_m=0.05,
        flame_temperature_k=1800.0,
        kinematic_viscosity_m2_s=nu_gw,
    )
    # Grashof should be around 1.35e6
    assert 1.0e6 < gr_gw < 2.0e6

    # Buoyancy factor Phi(Gr) = 1 / (1 + (Gr / 10^6)^0.4)
    phi_gw = EAFHIEngine.calculate_buoyancy_factor(gr_gw)
    assert 0.40 <= phi_gw <= 0.60

    # In zero microgravity: Gr = 0, Phi = 1.0
    gr_zero = EAFHIEngine.calculate_grashof_number(gravity_ms2=0.0)
    assert gr_zero == 0.0
    phi_zero = EAFHIEngine.calculate_buoyancy_factor(gr_zero)
    assert phi_zero == 1.0

    # In terrestrial 1g (g = 9.81 m/s2, standard air): Gr is high (> 2e7), Phi is suppressed (< 0.25)
    _, _, nu_1g = EAFHIEngine.calculate_gas_properties(pressure_kpa=101.325, oxygen_percentage=21.0)
    gr_1g = EAFHIEngine.calculate_grashof_number(gravity_ms2=9.80665, kinematic_viscosity_m2_s=nu_1g)
    phi_1g = EAFHIEngine.calculate_buoyancy_factor(gr_1g)
    assert phi_1g < 0.25


def test_hypobaric_moc_calculation():
    # PMMA: LOI = 17.5%
    # At standard 101.325 kPa, 9.81 m/s2
    moc_std = EAFHIEngine.calculate_hypobaric_moc(
        limiting_oxygen_index_std=17.5,
        pressure_kpa=101.325,
        gravity_ms2=9.80665,
    )
    # Scaled MOC should be close to 14.5 - 17.5%
    assert 14.0 <= moc_std <= 18.0

    # At low pressure 56.5 kPa, MOC increases due to reduced flame enthalpy and species concentration
    moc_gw = EAFHIEngine.calculate_hypobaric_moc(
        limiting_oxygen_index_std=17.5,
        pressure_kpa=56.5,
        gravity_ms2=1.62,
    )
    assert moc_gw > moc_std


def test_eafhi_score_bounded_and_classes():
    # PMMA in Gateway (56.5 kPa, 34% O2, 0.166 g)
    res_pmma = EAFHIEngine.calculate_eafhi(
        material="pmma",
        pressure_kpa=56.5,
        oxygen_percentage=34.0,
        gravity_level="lunar_gravity (0.16 g)",
    )
    assert 0.0 <= res_pmma["eafhi_score"] <= 1.0
    assert res_pmma["flammability_class"] == "CLASS_4_CRITICAL_RISK"
    assert res_pmma["risk_category"] == "CRITICAL"
    assert res_pmma["is_flammable"] is True
    assert res_pmma["oxygen_margin_pct"] > 0

    # Teflon in Gateway
    res_teflon = EAFHIEngine.calculate_eafhi(
        material="teflon",
        pressure_kpa=56.5,
        oxygen_percentage=34.0,
        gravity_level="lunar_gravity (0.16 g)",
    )
    assert 0.0 <= res_teflon["eafhi_score"] <= 1.0
    assert res_teflon["eafhi_score"] < res_pmma["eafhi_score"]
    assert res_teflon["flammability_class"] in ("CLASS_1_LOW_RISK", "CLASS_2_MODERATE_RISK")
    assert res_teflon["is_flammable"] is False
    assert res_teflon["oxygen_margin_pct"] < 0


def test_eafhi_gateway_profile_all_materials():
    profile = EAFHIEngine.evaluate_gateway_profile()
    assert profile["atmosphere_name"] == "Artemis Lunar Gateway Exploration Atmosphere"
    assert profile["pressure_kpa"] == 56.5
    assert profile["oxygen_percentage"] == 34.0
    assert len(profile["material_evaluations"]) == len(SPACECRAFT_MATERIALS)
    assert profile["critical_risk_count"] >= 1
    assert "Polymethylmethacrylate" in profile["highest_risk_material"]
    assert "Teflon" in profile["lowest_risk_material"]
    assert "Artemis Lunar Gateway Evaluation" in profile["gateway_safety_summary"]


def test_eafhi_sensitivity_sweep_parameters():
    # Sweep oxygen percentage for PMMA
    sweep_o2 = EAFHIEngine.sensitivity_sweep(
        material="pmma",
        parameter_to_sweep="oxygen_percentage",
        min_value=15.0,
        max_value=45.0,
        steps=10,
    )
    assert len(sweep_o2["sweep_values"]) == 10
    assert len(sweep_o2["eafhi_scores"]) == 10
    assert len(sweep_o2["grashof_numbers"]) == 10
    assert len(sweep_o2["flammability_classes"]) == 10
    # Higher oxygen -> monotonically higher or equal EAFHI score
    assert sweep_o2["eafhi_scores"][-1] >= sweep_o2["eafhi_scores"][0]

    # Sweep pressure
    sweep_p = EAFHIEngine.sensitivity_sweep(
        material="nomex",
        parameter_to_sweep="pressure_kpa",
        min_value=30.0,
        max_value=120.0,
        steps=8,
    )
    assert len(sweep_p["sweep_values"]) == 8

    # Sweep gravity
    sweep_g = EAFHIEngine.sensitivity_sweep(
        material="pmma",
        parameter_to_sweep="gravity_ms2",
        min_value=0.01,
        max_value=10.0,
        steps=7,
    )
    assert len(sweep_g["sweep_values"]) == 7


def test_api_eafhi_calculate_endpoint(client: TestClient):
    payload = {
        "material": "pmma",
        "pressure_kpa": 56.5,
        "oxygen_percentage": 34.0,
        "gravity_level": "lunar_gravity (0.16 g)",
        "characteristic_length_m": 0.05,
        "ventilation_velocity_cm_s": 3.0,
    }
    res = client.post("/api/v1/safety/eafhi/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["material_key"] == "pmma"
    assert data["eafhi_score"] >= 0.0
    assert data["eafhi_score"] <= 1.0
    assert data["flammability_class"] == "CLASS_4_CRITICAL_RISK"
    assert data["is_flammable"] is True
    assert "gas_density_kg_m3" in data
    assert "grashof_number" in data
    assert "buoyancy_factor" in data
    assert "moc_percentage" in data


def test_api_eafhi_gateway_profile_endpoint(client: TestClient):
    res = client.get("/api/v1/safety/eafhi/gateway-profile")
    assert res.status_code == 200
    data = res.json()
    assert data["pressure_kpa"] == 56.5
    assert data["oxygen_percentage"] == 34.0
    assert len(data["material_evaluations"]) == 6
    assert data["critical_risk_count"] >= 1
    assert "gateway_safety_summary" in data


def test_api_eafhi_sensitivity_endpoint(client: TestClient):
    payload = {
        "material": "nomex",
        "parameter_to_sweep": "oxygen_percentage",
        "min_value": 18.0,
        "max_value": 40.0,
        "steps": 12,
    }
    res = client.post("/api/v1/safety/eafhi/sensitivity", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["material"] == "nomex"
    assert data["parameter_swept"] == "oxygen_percentage"
    assert len(data["sweep_values"]) == 12
    assert len(data["eafhi_scores"]) == 12
    assert "critical_threshold_value" in data


def test_api_eafhi_validation_errors(client: TestClient):
    # Invalid pressure (< 10 kPa)
    res_bad_p = client.post(
        "/api/v1/safety/eafhi/calculate",
        json={"material": "pmma", "pressure_kpa": 2.0},
    )
    assert res_bad_p.status_code == 422

    # Invalid oxygen (> 100%)
    res_bad_o2 = client.post(
        "/api/v1/safety/eafhi/calculate",
        json={"material": "pmma", "oxygen_percentage": 150.0},
    )
    assert res_bad_o2.status_code == 422
