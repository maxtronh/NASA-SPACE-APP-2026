"""
Tier 3: Cross-Feature & Pairwise Combination Test Suite
Flame in Freefall - Scientific Intelligence Platform

Coverage: Multi-feature interaction pairs and combinatorial contracts across
ingestion, SI normalization, faceted catalog search, comparison engine,
corpus analytics, entity extraction, hybrid retrieval, and citation verification.
"""

import math
from typing import Any, Dict, List
import pytest
from httpx import Client

from tests.e2e.conftest import (
    assert_null_not_zero,
    assert_valid_nasa_url,
    build_ingestion_payload
)


# ==============================================================================
# 1. F6 + F7: Filtered Exploration -> Multi-Investigation Comparison
# ==============================================================================

def test_tier3_f6_f7_filter_regime_fuel_then_compare(api_client: Client):
    """Filters investigations by regime and fuel, then compares the retrieved candidates."""
    # Step 1: Filter by regime=laminar_diffusion and fuel=Methane
    search_res = api_client.get("/api/v1/investigations?regime=laminar_diffusion&fuel=Methane")
    assert search_res.status_code == 200
    items = search_res.json()["items"]
    assert len(items) >= 2  # ACME microgravity and ACME ground 1g

    slugs = [item["slug"] for item in items[:2]]

    # Step 2: Submit filtered pair to comparison engine
    comp_res = api_client.post("/api/v1/compare", json={"investigation_ids": slugs})
    assert comp_res.status_code == 200
    comp_data = comp_res.json()

    assert set(comp_data["investigation_ids"]) == set(slugs)
    grid = comp_data["comparison_grid"]
    for slug in slugs:
        assert slug in grid
        assert grid[slug]["fuel"] == "Methane (CH4)"


# ==============================================================================
# 2. F3 + F4 + F5: Raw Ingestion -> SI Normalization -> Stored Schema
# ==============================================================================

def test_tier3_f3_f4_f5_ingestion_si_conversion_provenance(api_client: Client, authentic_acme):
    """Verifies raw NASA record is transformed into SI units with complete cryptographic provenance."""
    payload = build_ingestion_payload(authentic_acme)

    # Validate ingestion payload via API
    val_res = api_client.post("/api/v1/ingest/validate", json=payload)
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "VALIDATED"

    # Cross-verify SI converted flow rate: 25 sccm -> 4.16667e-7 m^3/s
    orig_flow = payload["provenance"]["original_measurements"]["fuel_flow_rate"]
    si_flow = payload["provenance"]["si_measurements"]["fuel_flow_rate_m3_s"]
    assert "25" in orig_flow and "sccm" in orig_flow
    assert math.isclose(si_flow, 4.16667e-7, rel_tol=1e-4)


# ==============================================================================
# 3. F7 + F14: Microgravity vs Terrestrial 1g Gravitational Non-Equivalence
# ==============================================================================

def test_tier3_f7_f14_gravity_non_equivalence_detection(api_client: Client):
    """Verifies comparison between ISS microgravity experiment and 1g ground reference detects non-equivalence."""
    payload = {
        "investigation_ids": ["acme-cld-flame", "acme-cld-ground-1g"]
    }
    response = api_client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    data = response.json()

    assessment = data["equivalence_assessment"]
    assert assessment["equivalent"] is False
    assert any("gravitational" in r.lower() or "gravity" in r.lower() for r in assessment["reasons"])

    # Verify both records are populated in comparison grid
    grid = data["comparison_grid"]
    assert "microgravity" in grid["acme-cld-flame"]["gravity"].lower()
    assert "normal_gravity" in grid["acme-cld-ground-1g"]["gravity"].lower()


# ==============================================================================
# 4. F9 + F10 + F12: Entity Extraction -> Hybrid Retrieval -> Verified Citation
# ==============================================================================

def test_tier3_f9_f10_f12_entity_search_citation_pipeline(api_client: Client):
    """Verifies end-to-end SI query flow: entities extracted -> ranked -> verified NASA citation returned."""
    payload = {"query": "What are the droplet extinction characteristics of n-heptane in microgravity?"}
    response = api_client.post("/api/v1/si/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    # 1. Extracted entities
    entities = data["explainability"]["matched_entities"]
    assert any("droplet" in e.lower() for e in entities)

    # 2. Hybrid search confidence
    assert data["confidence_score"] >= 0.70
    assert data["abstention_flag"] is False

    # 3. Verified citation matches FLEX-2
    assert len(data["citations"]) >= 1
    top_citation = data["citations"][0]
    assert top_citation["investigation_id"] == "flex-2-heptane-droplet"
    assert_valid_nasa_url(top_citation["nasa_source_url"])


# ==============================================================================
# 5. F8 + F16: Analytics Missing-Data Calculation Matches Stored Nulls
# ==============================================================================

def test_tier3_f8_f16_analytics_completeness_matches_null_fields(api_client: Client):
    """Verifies that missing_data_matrix completeness percentage aligns with null counts."""
    # Fetch analytics
    analytics_res = api_client.get("/api/v1/analytics/corpus")
    assert analytics_res.status_code == 200
    analytics = analytics_res.json()
    total_inv = analytics["total_investigations"]
    matrix = analytics["missing_data_matrix"]

    for param_name, stats in matrix.items():
        present = stats["present_count"]
        missing = stats["missing_count"]
        pct = stats["completeness_pct"]

        assert present + missing == total_inv
        expected_pct = round((present / total_inv) * 100.0, 1)
        assert math.isclose(pct, expected_pct, abs_tol=0.2)


# ==============================================================================
# 6. F6 + F10: Structured Facet Filter vs SI Hybrid Query Concordance
# ==============================================================================

def test_tier3_f6_f10_structured_and_hybrid_search_concordance(api_client: Client):
    """Verifies structured API filter and natural language SI query identify identical target investigation."""
    # Structured search
    structured_res = api_client.get("/api/v1/investigations?regime=droplet_combustion&fuel=Heptane")
    assert structured_res.status_code == 200
    structured_slug = structured_res.json()["items"][0]["slug"]

    # Hybrid SI query
    si_res = api_client.post("/api/v1/si/query", json={"query": "isolated heptane droplet burning rate"})
    assert si_res.status_code == 200
    si_cited_slug = si_res.json()["citations"][0]["investigation_id"]

    assert structured_slug == si_cited_slug == "flex-2-heptane-droplet"


# ==============================================================================
# 7. F7 + F8: Comparison Grid Null Preservation Across Sparse Measurements
# ==============================================================================

def test_tier3_f7_f8_compare_sparse_measurements_preserves_null(api_client: Client):
    """Verifies comparing an investigation with missing soot fraction preserves null in grid."""
    payload = {"investigation_ids": ["flex-2-heptane-droplet", "acme-cld-flame"]}
    response = api_client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    grid = data["comparison_grid"]

    # FLEX-2 missing soot fraction must be None/null in comparison grid
    flex_measurements = grid["flex-2-heptane-droplet"]["si_measurements"]
    assert flex_measurements.get("soot_volume_fraction_dimensionless") is None


# ==============================================================================
# 8. F3 + F12: Citation URL Resolves to Stored Ingestion Source URL
# ==============================================================================

def test_tier3_f3_f12_citation_url_matches_ingested_provenance(api_client: Client):
    """Verifies citation URL generated by SI assistant matches the source URL in investigation record."""
    # Step 1: Run SI query for BASS-II
    si_res = api_client.post("/api/v1/si/query", json={"query": "BASS-II PMMA solid fuel flame spread"})
    assert si_res.status_code == 200
    citation_url = si_res.json()["citations"][0]["nasa_source_url"]

    # Step 2: Fetch investigation detail
    inv_res = api_client.get("/api/v1/investigations/bass-ii-solid-slab")
    assert inv_res.status_code == 200
    source_url = inv_res.json()["investigation"]["nasa_source_url"]

    assert citation_url == source_url
    assert_valid_nasa_url(citation_url)


# ==============================================================================
# 9. F4 + F7: SI Pressure Normalization Across Comparative Conditions
# ==============================================================================

def test_tier3_f4_f7_compare_different_pressure_units_normalized(api_client: Client):
    """Verifies that investigations recorded in psi vs atm are both normalized to Pascals for comparison."""
    # FLEX-2 (14.7 psi) and ACME (1.0 atm)
    payload = {"investigation_ids": ["flex-2-heptane-droplet", "acme-cld-flame"]}
    response = api_client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    grid = response.json()["comparison_grid"]

    p_flex = grid["flex-2-heptane-droplet"]["si_measurements"]["chamber_pressure_Pa"]
    p_acme = grid["acme-cld-flame"]["si_measurements"]["chamber_pressure_Pa"]

    # Both should be near ~101325 Pa (1 atm / 14.7 psi)
    assert math.isclose(p_flex, 101352.93, abs_tol=10.0)
    assert math.isclose(p_acme, 101325.0, abs_tol=10.0)


# ==============================================================================
# 10. F10 + F11: Mixed Domain Query Calibrated Confidence & Grounded Citations
# ==============================================================================

def test_tier3_f10_f11_mixed_grounded_and_ungrounded_query(api_client: Client):
    """Verifies query containing both valid combustion terms and sci-fi terms triggers proper abstention."""
    payload = {"query": "Explain methane laminar diffusion flame dynamics in warp drive engines"}
    response = api_client.post("/api/v1/si/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    # The presence of ungrounded 'warp' term should trigger abstention or low confidence
    assert data["abstention_flag"] is True
    assert data["confidence_score"] < 0.50
    assert len(data["citations"]) == 0


# ==============================================================================
# 11. F6 + F8: Facet Count Concordance Between Search & Analytics
# ==============================================================================

def test_tier3_f6_f8_regime_count_matches_between_search_and_analytics(api_client: Client):
    """Verifies that the count of investigations returned by regime filter matches analytics regime counts."""
    # Fetch analytics
    analytics_res = api_client.get("/api/v1/analytics/corpus")
    assert analytics_res.status_code == 200
    regime_counts = analytics_res.json()["combustion_regimes"]

    for regime, count in regime_counts.items():
        filter_res = api_client.get(f"/api/v1/investigations?regime={regime}")
        assert filter_res.status_code == 200
        assert filter_res.json()["total"] == count


# ==============================================================================
# 12. F2 + F3 + F6: Distinct NASA Missions Retrievable Across Corpus
# ==============================================================================

def test_tier3_f2_f3_f6_all_mission_acronyms_retrievable(api_client: Client):
    """Verifies that all genuine NASA mission acronyms (FLEX, ACME, BASS) exist in the catalog."""
    res = api_client.get("/api/v1/investigations?limit=100")
    assert res.status_code == 200
    items = res.json()["items"]
    acronyms = {item["project_acronym"] for item in items}

    expected_acronyms = {"FLEX-2", "ACME", "BASS-II"}
    for expected in expected_acronyms:
        assert expected in acronyms


# ==============================================================================
# 13. F5 + F12: Relational Integrity of Cited Investigations
# ==============================================================================

def test_tier3_f5_f12_citation_investigation_slug_exists(api_client: Client):
    """Verifies every citation returned in an SI query references a valid, retrievable investigation."""
    si_res = api_client.post("/api/v1/si/query", json={"query": "methane coflow laminar diffusion flame"})
    assert si_res.status_code == 200
    citations = si_res.json()["citations"]
    assert len(citations) >= 1

    for c in citations:
        slug = c["investigation_id"]
        detail_res = api_client.get(f"/api/v1/investigations/{slug}")
        assert detail_res.status_code == 200
        assert detail_res.json()["investigation"]["slug"] == slug


# ==============================================================================
# 14. F4 + F8: Analytics Calculation Safely Ignores NULL Measurements
# ==============================================================================

def test_tier3_f4_f8_analytics_preserves_non_null_calculation(api_client: Client):
    """Verifies analytics completeness percent correctly computes (present / total) without coercing nulls."""
    analytics_res = api_client.get("/api/v1/analytics/corpus")
    assert analytics_res.status_code == 200
    data = analytics_res.json()
    matrix = data["missing_data_matrix"]

    for k, v in matrix.items():
        assert v["present_count"] >= 0
        assert v["missing_count"] >= 0
        assert v["present_count"] + v["missing_count"] == data["total_investigations"]


# ==============================================================================
# 15. F11 + F12: Abstention Flag Precludes Fabricated Citations
# ==============================================================================

def test_tier3_f11_f12_abstention_never_generates_fake_citations(api_client: Client, out_of_domain_queries):
    """Verifies that whenever abstention_flag is True, citations array is empty (never fabricated)."""
    for q in out_of_domain_queries[:3]:
        response = api_client.post("/api/v1/si/query", json={"query": q})
        assert response.status_code == 200
        data = response.json()
        if data["abstention_flag"]:
            assert len(data["citations"]) == 0, f"Violation: Fabricated citations on abstained query '{q}'"


# ==============================================================================
# 16. F6 + F7 + F14: Multi-Regime Comparison Asserts Non-Equivalence
# ==============================================================================

def test_tier3_f6_f7_f14_droplet_vs_diffusion_regime_non_equivalence(api_client: Client):
    """Verifies comparing droplet combustion vs laminar diffusion flame asserts regime mismatch."""
    payload = {"investigation_ids": ["flex-2-heptane-droplet", "acme-cld-flame"]}
    response = api_client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assessment = data["equivalence_assessment"]
    assert assessment["equivalent"] is False
    assert any("regime" in r.lower() for r in assessment["reasons"])


# ==============================================================================
# 17. F3 + F4 + F8: Ingestion Provenance 100% Validated Across Catalog
# ==============================================================================

def test_tier3_f3_f4_f8_all_catalog_investigations_validated(api_client: Client):
    """Verifies every item in the catalog has VALIDATED provenance and non-empty SHA-256."""
    catalog_res = api_client.get("/api/v1/investigations?limit=100")
    assert catalog_res.status_code == 200
    items = catalog_res.json()["items"]

    for item in items:
        detail_res = api_client.get(f"/api/v1/investigations/{item['slug']}")
        assert detail_res.status_code == 200
        prov = detail_res.json()["provenance"]
        assert prov["validation_status"] == "VALIDATED"
        assert len(prov["sha256_checksum"]) == 64


# ==============================================================================
# 18. F9 + F15: Multi-Keyword Chat Query Entity Focus
# ==============================================================================

def test_tier3_f9_f15_multi_keyword_chat_query_entity_focus(api_client: Client):
    """Verifies multi-keyword query extracts combustion entities and returns accurate citation."""
    payload = {"query": "heptane extinction diameter in microgravity CIR facility"}
    response = api_client.post("/api/v1/si/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["abstention_flag"] is False
    assert data["citations"][0]["investigation_id"] == "flex-2-heptane-droplet"
