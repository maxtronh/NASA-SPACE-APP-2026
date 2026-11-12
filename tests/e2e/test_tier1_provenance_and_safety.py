"""Tier 1 Opaque Tests for Merkle Provenance and NASA-STD-6001B Flammability Safety Endpoints."""

import pytest
from starlette.testclient import TestClient


def test_tier1_merkle_provenance_e2e_contract(api_client: TestClient):
    """Verifies Merkle root generation and cryptographic inclusion proof verification."""
    # 1. Fetch root
    root_res = api_client.get("/api/v1/provenance/merkle-root")
    assert root_res.status_code == 200
    root_data = root_res.json()
    assert "merkle_root" in root_data
    assert len(root_data["merkle_root"]) == 64
    assert root_data["total_leaves"] >= 5

    # 2. Fetch proof for BASS-II investigation
    proof_res = api_client.get("/api/v1/provenance/proof/bass-ii-solid-slab")
    assert proof_res.status_code == 200
    proof_data = proof_res.json()
    assert proof_data["identifier"] == "bass-ii-solid-slab"
    assert "leaf_hash" in proof_data
    assert "proof" in proof_data
    assert proof_data["verified"] is True

    # 3. Verify inclusion proof via POST endpoint
    verify_payload = {
        "leaf_hash": proof_data["leaf_hash"],
        "proof": proof_data["proof"],
        "expected_root": root_data["merkle_root"],
    }
    verify_res = api_client.post("/api/v1/provenance/verify-proof", json=verify_payload)
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True


def test_tier1_nasa_std_6001b_safety_e2e_contract(api_client: TestClient):
    """Verifies NASA-STD-6001B materials catalog and evaluation compliance contracts."""
    # 1. List materials
    m_res = api_client.get("/api/v1/safety/materials")
    assert m_res.status_code == 200
    materials = m_res.json()["materials"]
    keys = [m["key"] for m in materials]
    assert "pmma" in keys
    assert "nomex" in keys

    # 2. Evaluate PMMA in standard cabin vs exploration atmosphere
    eval_payload = {
        "material": "pmma",
        "oxygen_percentage": 21.0,
        "pressure_kpa": 101.325,
        "thickness_mm": 2.0,
    }
    eval_res = api_client.post("/api/v1/safety/evaluate", json=eval_payload)
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert "limiting_oxygen_index" in data
    assert "test_1_upward_propagation" in data
    assert "test_7_heat_release" in data
    assert "overall_compliance" in data
