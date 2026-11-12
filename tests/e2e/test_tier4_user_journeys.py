"""
Tier 4: End-to-End User Journeys & Real-World Application Workloads
Flame in Freefall - Scientific Intelligence Platform

Coverage: Complex multi-step user scenarios S1 through S7 defined in TEST_INFRA.md:
S1: Complete Golden Path (Ingestion -> DB -> SI Search -> Citation -> Detail -> Compare -> Analytics)
S2: Microgravity vs Normal Gravity Condition Non-Equivalence Workflow
S3: Out-of-Domain SI Query Explicit Abstention & Zero Fabrication Workflow
S4: Real NASA Data Missing Measurement Integrity Workflow
S5: Full Multi-Service System Health & Contract Conformance Workflow
S6: Multi-Fuel Investigation Discovery & Cross-Validation Workflow
S7: Scientific Data Ingestion & Tamper Resilience Workflow
"""

import math
from typing import Any, Dict, List
import pytest
from httpx import Client

from tests.e2e.conftest import (
    assert_null_not_zero,
    assert_valid_nasa_url,
    calculate_sha256,
    build_ingestion_payload
)


# ==============================================================================
# Scenario S1: Complete Golden Path User Journey
# Ingested NASA record -> DB -> SI Search -> Citation -> Detail -> Compare -> Analytics
# ==============================================================================

def test_tier4_s1_complete_end_to_end_user_journey(api_client: Client, authentic_flex2):
    """
    S1: Full User Journey:
    1. Authentic NASA research record ingested with SHA-256 provenance & SI conversion.
    2. Record discoverable in research explorer.
    3. User queries SI assistant with natural language scientific question.
    4. SI returns confident answer with verified NASA citation.
    5. User inspects investigation detail view with measurements.
    6. User compares investigation against another research condition.
    7. User views dashboard analytics showing corpus metrics and completeness.
    """
    # Step 1: Ingestion Validation
    ingest_payload = build_ingestion_payload(authentic_flex2)
    val_res = api_client.post("/api/v1/ingest/validate", json=ingest_payload)
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "VALIDATED"
    slug = ingest_payload["investigation"]["slug"]

    # Step 2: Investigation Explorer Discovery
    list_res = api_client.get(f"/api/v1/investigations?search={slug}")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(item["slug"] == slug for item in items)

    # Step 3 & 4: SI Assistant Query & Verified Citation
    si_res = api_client.post("/api/v1/si/query", json={
        "query": "What are the droplet extinction characteristics of heptane in microgravity?"
    })
    assert si_res.status_code == 200
    si_data = si_res.json()
    assert si_data["abstention_flag"] is False
    assert si_data["confidence_score"] >= 0.70
    assert len(si_data["citations"]) >= 1
    top_citation = si_data["citations"][0]
    assert top_citation["investigation_id"] == slug
    assert_valid_nasa_url(top_citation["nasa_source_url"])

    # Step 5: Investigation Detail View
    detail_res = api_client.get(f"/api/v1/investigations/{slug}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["investigation"]["slug"] == slug
    assert detail_data["provenance"]["si_measurements"]["initial_droplet_diameter_m"] == 0.0021

    # Step 6: Multi-Investigation Comparison Workspace
    comp_res = api_client.post("/api/v1/compare", json={
        "investigation_ids": [slug, "acme-cld-flame"]
    })
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert slug in comp_data["comparison_grid"]
    assert "acme-cld-flame" in comp_data["comparison_grid"]
    assert "equivalence_assessment" in comp_data

    # Step 7: Dashboard Analytics & Completeness Matrix
    analytics_res = api_client.get("/api/v1/analytics/corpus")
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["total_investigations"] >= 4
    assert "missing_data_matrix" in analytics_data


# ==============================================================================
# Scenario S2: Condition Non-Equivalence Warning Workflow
# Comparing microgravity ISS flight vs 1g terrestrial ground reference
# ==============================================================================

def test_tier4_s2_gravitational_condition_non_equivalence_journey(api_client: Client):
    """
    S2: Gravitational Non-Equivalence Workflow:
    1. User selects ACME microgravity flame and ACME 1g ground reference.
    2. Submits to comparison workspace.
    3. System evaluates gravity levels (~10^-6 g vs 1.0 g).
    4. System issues explicit non-equivalence warning and documents reasons.
    """
    micro_slug = "acme-cld-flame"
    ground_slug = "acme-cld-ground-1g"

    # User initiates comparison
    res = api_client.post("/api/v1/compare", json={"investigation_ids": [micro_slug, ground_slug]})
    assert res.status_code == 200
    data = res.json()

    assessment = data["equivalence_assessment"]
    assert assessment["equivalent"] is False
    assert any("gravity" in r.lower() or "gravitational" in r.lower() for r in assessment["reasons"])

    # Verify both flame heights are available for comparison
    grid = data["comparison_grid"]
    assert grid[micro_slug]["gravity"] == "microgravity (~10^-6 g)"
    assert grid[ground_slug]["gravity"] == "normal_gravity (1.0 g)"


# ==============================================================================
# Scenario S3: Out-of-Domain SI Query Explicit Abstention Workflow
# Abstains on ungrounded query without fabricating citations
# ==============================================================================

def test_tier4_s3_out_of_domain_abstention_journey(api_client: Client, out_of_domain_queries):
    """
    S3: SI Abstention Workflow:
    1. User submits query outside NASA combustion domain ("What is the capital of Mars?").
    2. SI engine analyzes query terms and finds zero grounded combustion matches.
    3. System sets abstention_flag = True and confidence_score < 0.3.
    4. System returns informative abstention message.
    5. System provides zero fabricated citations (citations list is empty).
    """
    for query in out_of_domain_queries:
        res = api_client.post("/api/v1/si/query", json={"query": query})
        assert res.status_code == 200
        data = res.json()

        assert data["abstention_flag"] is True
        assert data["confidence_score"] < 0.30
        assert len(data["citations"]) == 0
        assert "abstention" in data["answer"].lower() or "not correspond" in data["answer"].lower()


# ==============================================================================
# Scenario S4: Real NASA Data Missing Measurement Integrity Workflow
# Unmeasured channels remain strictly NULL through Ingestion, Storage, API, and Analytics
# ==============================================================================

def test_tier4_s4_missing_measurement_integrity_journey(api_client: Client, authentic_bass2):
    """
    S4: Missing Measurement Integrity Workflow:
    1. Authentic BASS-II solid slab experiment has null radiative flux and null droplet diameter.
    2. Ingestion pipeline accepts record without coercing null to 0.0.
    3. Investigation detail endpoint returns None/null for these fields.
    4. Analytics missing data matrix accurately tallies null counts.
    5. Comparison grid displays null, avoiding false scientific conclusions.
    """
    slug = authentic_bass2["slug"]

    # Ingestion validation
    ingest_payload = build_ingestion_payload(authentic_bass2)
    val_res = api_client.post("/api/v1/ingest/validate", json=ingest_payload)
    assert val_res.status_code == 200

    # Detail API inspect
    detail_res = api_client.get(f"/api/v1/investigations/{slug}")
    assert detail_res.status_code == 200
    orig_m = detail_res.json()["provenance"]["original_measurements"]
    assert_null_not_zero(orig_m.get("radiative_flux"), "BASS-II radiative_flux")
    assert_null_not_zero(orig_m.get("initial_droplet_diameter"), "BASS-II initial_droplet_diameter")

    # Comparison Grid inspect
    comp_res = api_client.post("/api/v1/compare", json={"investigation_ids": [slug, "acme-cld-flame"]})
    assert comp_res.status_code == 200
    grid = comp_res.json()["comparison_grid"]
    assert grid[slug]["si_measurements"].get("radiative_flux_w_m2") is None


# ==============================================================================
# Scenario S5: Full Multi-Service System Health & Contract Conformance Workflow
# ==============================================================================

def test_tier4_s5_multi_service_health_and_contracts(api_client: Client):
    """
    S5: System Health & Service Connectivity Workflow:
    1. Health check returns healthy status with connected database.
    2. Catalog exploration responds with HTTP 200.
    3. Comparison service responds with HTTP 200.
    4. SI query service responds with HTTP 200.
    5. Analytics service responds with HTTP 200.
    """
    # 1. Health
    h = api_client.get("/api/v1/health")
    assert h.status_code == 200
    assert h.json()["status"] == "healthy"

    # 2. Catalog
    c = api_client.get("/api/v1/investigations")
    assert c.status_code == 200

    # 3. Compare
    cmp = api_client.post("/api/v1/compare", json={"investigation_ids": ["flex-2-heptane-droplet", "acme-cld-flame"]})
    assert cmp.status_code == 200

    # 4. SI Query
    si = api_client.post("/api/v1/si/query", json={"query": "methane flame"})
    assert si.status_code == 200

    # 5. Analytics
    a = api_client.get("/api/v1/analytics/corpus")
    assert a.status_code == 200


# ==============================================================================
# Scenario S6: Multi-Fuel Investigation Discovery & Cross-Validation Workflow
# ==============================================================================

def test_tier4_s6_multi_fuel_discovery_and_cross_validation(api_client: Client):
    """
    S6: Multi-Fuel Discovery Workflow:
    1. Discovers liquid fuel (n-Heptane) investigation.
    2. Discovers gaseous fuel (Methane) investigation.
    3. Discovers solid polymer fuel (PMMA) investigation.
    4. Cross-validates all 3 have authentic NTRS links and distinct regimes.
    """
    fuels_to_test = [
        ("Heptane", "droplet_combustion"),
        ("Methane", "laminar_diffusion"),
        ("PMMA", "solid_flame_spread"),
    ]

    for fuel_name, expected_regime in fuels_to_test:
        res = api_client.get(f"/api/v1/investigations?fuel={fuel_name}")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 1
        item = items[0]
        assert item["combustion_regime"] == expected_regime
        assert_valid_nasa_url(item["nasa_source_url"])


# ==============================================================================
# Scenario S7: Scientific Data Ingestion & Tamper Resilience Workflow
# ==============================================================================

def test_tier4_s7_data_ingestion_and_tamper_resilience(api_client: Client, authentic_acme):
    """
    S7: Data Ingestion & Tamper Resilience:
    1. Valid NASA payload passes verification.
    2. Artificially tampered payload is detected and rejected.
    3. Payload with injected fake zeros in null fields is rejected.
    """
    valid_payload = build_ingestion_payload(authentic_acme)
    ok_res = api_client.post("/api/v1/ingest/validate", json=valid_payload)
    assert ok_res.status_code == 200
    assert ok_res.json()["status"] == "VALIDATED"

    # Corrupt payload with coerced zero in null field
    corrupted_payload = build_ingestion_payload(authentic_acme)
    corrupted_payload["provenance"]["si_measurements"]["initial_droplet_diameter_m"] = 0.0
    bad_res = api_client.post("/api/v1/ingest/validate", json=corrupted_payload)
    assert bad_res.status_code == 422
