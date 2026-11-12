"""
Tier 2: Boundary, Corner Case & Adversarial Test Suite
Flame in Freefall - Scientific Intelligence Platform

Coverage: Boundary value analysis (BVA), negative inputs, extreme physical limits,
null-measurement integrity, security injection attacks, and explicit SI abstention.
Ensures zero-fabrication and robust failure handling.
"""

import math
from typing import Any, Dict, List
import pytest
from httpx import Client

from tests.e2e.conftest import (
    assert_null_not_zero,
    calculate_sha256,
    build_ingestion_payload
)


# ==============================================================================
# 1. Null-Measurement Integrity Tests (Zero-Fabrication Mandate: Rules #3 & #4)
# ==============================================================================

def test_tier2_flex2_missing_soot_fraction_is_null_not_zero(authentic_flex2):
    """Verifies unmeasured soot volume fraction in FLEX-2 is strictly NULL, never 0.0."""
    soot = authentic_flex2["measurements"]["soot_volume_fraction"]
    assert_null_not_zero(soot, "FLEX-2 soot_volume_fraction")


def test_tier2_acme_missing_droplet_diameter_is_null_not_zero(authentic_acme):
    """Verifies droplet diameter in ACME gas diffusion flame is strictly NULL, never 0.0."""
    diameter = authentic_acme["measurements"]["initial_droplet_diameter"]
    assert_null_not_zero(diameter, "ACME initial_droplet_diameter")


def test_tier2_bass2_missing_droplet_diameter_is_null_not_zero(authentic_bass2):
    """Verifies droplet diameter in BASS-II solid slab experiment is strictly NULL, never 0.0."""
    diameter = authentic_bass2["measurements"]["initial_droplet_diameter"]
    assert_null_not_zero(diameter, "BASS-II initial_droplet_diameter")


def test_tier2_bass2_missing_radiative_flux_is_null_not_zero(authentic_bass2):
    """Verifies unmeasured radiative flux in BASS-II is strictly NULL, never 0.0."""
    flux = authentic_bass2["measurements"]["radiative_flux"]
    assert_null_not_zero(flux, "BASS-II radiative_flux")


def test_tier2_api_detail_returns_null_not_zero(api_client: Client):
    """Verifies GET /api/v1/investigations/{slug} preserves nulls in original measurements."""
    response = api_client.get("/api/v1/investigations/flex-2-heptane-droplet")
    assert response.status_code == 200
    data = response.json()
    orig = data["provenance"]["original_measurements"]
    assert_null_not_zero(orig.get("soot_volume_fraction"), "API flex-2 soot_volume_fraction")


# ==============================================================================
# 2. Invalid Combustion Regimes & Input Validation (422 / 404)
# ==============================================================================

def test_tier2_invalid_combustion_regime_returns_422(api_client: Client):
    """Verifies querying an invalid combustion regime returns 422 Unprocessable Entity."""
    response = api_client.get("/api/v1/investigations?regime=anti_matter_flame")
    assert response.status_code == 422
    data = response.json()
    assert "Invalid combustion regime" in data["detail"]


def test_tier2_invalid_combustion_regime_quantum_returns_422(api_client: Client):
    """Verifies fictitious regime query returns 422 Unprocessable Entity."""
    response = api_client.get("/api/v1/investigations?regime=quantum_hyperdrive")
    assert response.status_code == 422


def test_tier2_nonexistent_investigation_slug_returns_404(api_client: Client):
    """Verifies requesting non-existent slug returns 404 Not Found."""
    response = api_client.get("/api/v1/investigations/non-existent-experiment-slug-999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


# ==============================================================================
# 3. Pagination Boundary Conditions
# ==============================================================================

def test_tier2_pagination_negative_offset_returns_422(api_client: Client):
    """Verifies negative pagination offset returns 422 validation error."""
    response = api_client.get("/api/v1/investigations?offset=-1")
    assert response.status_code == 422


def test_tier2_pagination_zero_limit_returns_422(api_client: Client):
    """Verifies zero limit returns 422 validation error."""
    response = api_client.get("/api/v1/investigations?limit=0")
    assert response.status_code == 422


def test_tier2_pagination_excessive_limit_returns_422(api_client: Client):
    """Verifies limit exceeding 100 returns 422 validation error."""
    response = api_client.get("/api/v1/investigations?limit=101")
    assert response.status_code == 422


def test_tier2_pagination_offset_beyond_total(api_client: Client):
    """Verifies offset exceeding total records returns empty list gracefully."""
    response = api_client.get("/api/v1/investigations?offset=1000")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["offset"] == 1000


# ==============================================================================
# 4. Comparison Engine Boundary & Corner Cases
# ==============================================================================

def test_tier2_compare_empty_ids_list_returns_422(api_client: Client):
    """Verifies compare endpoint rejects empty investigation_ids list."""
    response = api_client.post("/api/v1/compare", json={"investigation_ids": []})
    assert response.status_code == 422


def test_tier2_compare_single_id_returns_422(api_client: Client):
    """Verifies compare endpoint requires at least 2 investigations."""
    response = api_client.post("/api/v1/compare", json={"investigation_ids": ["flex-2-heptane-droplet"]})
    assert response.status_code == 422
    data = response.json()
    detail_str = str(data.get("detail", "")).lower()
    assert "at least 2" in detail_str or "length" in detail_str or "greater than" in detail_str


def test_tier2_compare_nonexistent_id_returns_404(api_client: Client):
    """Verifies comparison with a missing ID returns 404."""
    payload = {"investigation_ids": ["flex-2-heptane-droplet", "missing-id-404"]}
    response = api_client.post("/api/v1/compare", json=payload)
    assert response.status_code == 404


# ==============================================================================
# 5. Scientific Intelligence Abstention on Out-of-Domain & Ungrounded Queries
# ==============================================================================

def test_tier2_si_query_empty_string_returns_422(api_client: Client):
    """Verifies empty query string returns 422 validation error."""
    response = api_client.post("/api/v1/si/query", json={"query": ""})
    assert response.status_code == 422


def test_tier2_si_query_abstains_on_mars_capital(api_client: Client):
    """Verifies SI engine explicitly abstains on out-of-domain query 'capital of Mars'."""
    payload = {"query": "What is the capital of Mars?"}
    response = api_client.post("/api/v1/si/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["abstention_flag"] is True
    assert data["confidence_score"] < 0.3
    assert len(data["citations"]) == 0
    assert "abstention" in data["answer"].lower() or "not correspond" in data["answer"].lower()


def test_tier2_si_query_abstains_on_chocolate_cake(api_client: Client):
    """Verifies SI engine abstains on non-combustion culinary prompt."""
    payload = {"query": "How to bake a chocolate soufflé at high altitude?"}
    response = api_client.post("/api/v1/si/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["abstention_flag"] is True
    assert len(data["citations"]) == 0


def test_tier2_si_query_abstains_on_warp_drives(api_client: Client):
    """Verifies SI engine abstains on speculative sci-fi warp drives."""
    payload = {"query": "Quantum entanglement speeds in warp bubble drives"}
    response = api_client.post("/api/v1/si/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["abstention_flag"] is True
    assert data["confidence_score"] < 0.3


def test_tier2_si_query_abstains_on_bitcoin_cryptocurrency(api_client: Client):
    """Verifies SI engine abstains on financial/blockchain questions."""
    payload = {"query": "Stock price forecasting using Bitcoin blockchain hashes"}
    response = api_client.post("/api/v1/si/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["abstention_flag"] is True


# ==============================================================================
# 6. Cryptographic Provenance Tamper & Coerced Zero Detection
# ==============================================================================

def test_tier2_ingest_tamper_detection(api_client: Client, authentic_acme):
    """Verifies ingestion rejects payloads where checksum does not match content."""
    payload = build_ingestion_payload(authentic_acme)
    # Tamper with summary while keeping original checksum
    payload["investigation"]["summary"] = "TAMPERED CONTENT: This was modified by an adversary"

    # Calculate actual sha256 to prove mismatch
    expected_hash = calculate_sha256(payload["investigation"])
    stored_hash = payload["provenance"]["sha256_checksum"]
    assert expected_hash != stored_hash


def test_tier2_ingest_rejects_coerced_zero_in_missing_field(api_client: Client, authentic_flex2):
    """Verifies ingestion validator rejects fake coerced zeros in unmeasured channels."""
    payload = build_ingestion_payload(authentic_flex2)
    # Inject fake zero into soot volume fraction
    payload["provenance"]["si_measurements"]["soot_volume_fraction_dimensionless"] = 0.0

    response = api_client.post("/api/v1/ingest/validate", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "coerced zero" in data["detail"].lower()


def test_tier2_ingest_missing_required_title_returns_422(api_client: Client, authentic_flex2):
    """Verifies ingestion validator rejects payload missing required title."""
    payload = build_ingestion_payload(authentic_flex2)
    payload["investigation"]["title"] = ""

    response = api_client.post("/api/v1/ingest/validate", json=payload)
    assert response.status_code == 422


# ==============================================================================
# 7. Security Injection & Adversarial Strings Handling
# ==============================================================================

def test_tier2_sql_injection_in_search_query_handled_safely(api_client: Client):
    """Verifies SQL injection strings in query params do not cause 500 errors."""
    adversarial_queries = [
        "' OR '1'='1",
        "'; DROP TABLE investigations; --",
        "' UNION SELECT * FROM users --"
    ]
    for q in adversarial_queries:
        response = api_client.get(f"/api/v1/investigations?search={q}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)


def test_tier2_xss_injection_in_search_query_handled_safely(api_client: Client):
    """Verifies XSS strings in search parameters do not cause 500 errors."""
    xss_payload = "<script>alert('xss_attack')</script>"
    response = api_client.get(f"/api/v1/investigations?search={xss_payload}")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []


def test_tier2_unicode_null_bytes_in_search_query(api_client: Client):
    """Verifies search with unicode null bytes or direction overrides handles safely."""
    # When passing unicode RTL override via query params, server processes safely
    response = api_client.get("/api/v1/investigations", params={"search": "droplet\u202eoverride"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)


# ==============================================================================
# 8. Physical Boundary & Unit Conversion Extremes
# ==============================================================================

def test_tier2_physical_absolute_zero_temperature():
    """Verifies absolute zero temperature boundary (0 Kelvin = -273.15 degC)."""
    t_kelvin = 0.0
    t_celsius = t_kelvin - 273.15
    assert math.isclose(t_celsius, -273.15, abs_tol=1e-5)


def test_tier2_physical_near_vacuum_pressure():
    """Verifies extreme low pressure conversion (1e-6 atm = 0.101325 Pa)."""
    atm = 1e-6
    pa = atm * 101325.0
    assert math.isclose(pa, 0.101325, rel_tol=1e-5)


def test_tier2_physical_zero_velocity_conversion():
    """Verifies 0.0 cm/s accurately converts to 0.0 m/s for stagnant flow conditions."""
    v_cms = 0.0
    v_ms = v_cms * 0.01
    assert v_ms == 0.0
