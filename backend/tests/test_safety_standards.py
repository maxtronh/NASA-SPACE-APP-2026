"""Unit and integration tests for NASA-STD-6001B Spacecraft Materials Flammability Evaluation."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.safety.evaluator import FlammabilityEvaluator
from backend.app.safety.standards import CABIN_ATMOSPHERES, SPACECRAFT_MATERIALS


@pytest.fixture
def client():
    return TestClient(app)


def test_materials_and_cabin_standards_loaded():
    assert "pmma" in SPACECRAFT_MATERIALS
    assert "nomex" in SPACECRAFT_MATERIALS
    assert "teflon" in SPACECRAFT_MATERIALS
    assert SPACECRAFT_MATERIALS["pmma"].limiting_oxygen_index == 17.5
    assert SPACECRAFT_MATERIALS["teflon"].limiting_oxygen_index == 95.0

    assert "iss_standard" in CABIN_ATMOSPHERES
    assert "artemis_gateway" in CABIN_ATMOSPHERES
    assert CABIN_ATMOSPHERES["artemis_gateway"].oxygen_percentage == 34.0


def test_flammability_evaluator_pmma_fails_in_artemis():
    # PMMA in Artemis 34% O2 exploration atmosphere: exceeds burn length and drips
    result = FlammabilityEvaluator.evaluate(
        material_key="pmma",
        oxygen_percentage=34.0,
        pressure_kpa=56.5,
        thickness_mm=2.0,
    )
    assert result["overall_compliance"] == "NON_COMPLIANT"
    assert result["test_1_upward_propagation"]["status"] == "FAIL"
    assert result["oxygen_margin_pct"] < 0  # 17.5 - 34 = -16.5


def test_flammability_evaluator_nomex_passes_in_standard_air():
    # Nomex in ISS 21% O2: LOI is 29% -> self-extinguishes
    result = FlammabilityEvaluator.evaluate(
        material_key="nomex",
        oxygen_percentage=21.0,
        pressure_kpa=101.325,
        thickness_mm=1.5,
    )
    assert result["overall_compliance"] in ("COMPLIANT", "RESTRICTED_USE")
    assert result["test_1_upward_propagation"]["status"] == "PASS"
    assert result["test_1_upward_propagation"]["burn_length_cm"] < 15.24


def test_flammability_evaluator_teflon_always_compliant():
    # Teflon (LOI 95%) in hyperbaric conditions
    result = FlammabilityEvaluator.evaluate(
        material_key="teflon",
        oxygen_percentage=30.0,
        pressure_kpa=101.325,
    )
    assert result["overall_compliance"] == "COMPLIANT"
    assert result["test_1_upward_propagation"]["status"] == "PASS"
    assert result["test_7_heat_release"]["status"] == "PASS"


def test_api_list_materials_and_environments(client: TestClient):
    # Materials
    m_res = client.get("/api/v1/safety/materials")
    assert m_res.status_code == 200
    m_data = m_res.json()
    assert "materials" in m_data
    assert len(m_data["materials"]) >= 5

    # Environments
    e_res = client.get("/api/v1/safety/cabin-environments")
    assert e_res.status_code == 200
    e_data = e_res.json()
    assert "cabin_atmospheres" in e_data
    assert len(e_data["cabin_atmospheres"]) >= 4


def test_api_evaluate_material_safety_endpoint(client: TestClient):
    payload = {
        "material": "pmma",
        "oxygen_percentage": 21.0,
        "pressure_kpa": 101.325,
        "thickness_mm": 2.0,
        "gravity_level": "microgravity (~10^-6 g)",
        "ventilation_velocity_cm_s": 3.0,
    }
    res = client.post("/api/v1/safety/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "material_name" in data
    assert "test_1_upward_propagation" in data
    assert "test_7_heat_release" in data
    assert "overall_compliance" in data
    assert "safety_recommendation" in data


def test_api_evaluate_validation_errors(client: TestClient):
    # Invalid oxygen percentage
    res_o2 = client.post("/api/v1/safety/evaluate", json={"material": "nomex", "oxygen_percentage": 150.0})
    assert res_o2.status_code == 422

    # Unknown material
    res_unknown = client.post("/api/v1/safety/evaluate", json={"material": "unobtainium_crystal"})
    assert res_unknown.status_code == 422
