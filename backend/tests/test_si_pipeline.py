"""Comprehensive unit and integration tests for the authentic 7-stage ML and Scientific Intelligence pipeline."""

import math

import pytest
from fastapi import HTTPException

from backend.app.ml.abstention import AbstentionEngine
from backend.app.ml.citation_engine import CitationEngine
from backend.app.ml.embeddings import (
    VECTOR_DIMENSION,
    EmbeddingPipeline,
    _deterministic_projection,
)
from backend.app.ml.entity_extractor import ScientificEntityExtractor
from backend.app.ml.pipeline import ScientificIntelligencePipeline
from backend.app.ml.retriever import HybridRetriever
from backend.app.services.si_service import SIService

# ==============================================================================
# 1. Embedding Pipeline Tests
# ==============================================================================

def test_embedding_pipeline_generates_384_dim_normalized_vector():
    """Verifies that the embedding pipeline generates 384-dimensional unit-norm dense vectors."""
    pipeline = EmbeddingPipeline()
    vec = pipeline.embed_text("NASA microgravity droplet combustion experiment")
    assert len(vec) == VECTOR_DIMENSION
    assert isinstance(vec[0], float)

    norm = math.sqrt(sum(x * x for x in vec))
    assert math.isclose(norm, 1.0, abs_tol=1e-4)


def test_embedding_cosine_similarity():
    """Verifies cosine similarity calculations between identical and dissimilar texts."""
    pipeline = EmbeddingPipeline()
    v1 = pipeline.embed_text("n-heptane droplet burning in microgravity")
    v2 = pipeline.embed_text("n-heptane droplet burning in microgravity")
    v3 = pipeline.embed_text("completely unrelated culinary recipe for pasta")

    sim_identical = pipeline.cosine_similarity(v1, v2)
    assert math.isclose(sim_identical, 1.0, abs_tol=1e-4)

    sim_dissimilar = pipeline.cosine_similarity(v1, v3)
    assert sim_dissimilar < sim_identical


def test_deterministic_projection_fallback_resilience():
    """Verifies deterministic projection produces reproducible 384-d normalized vectors."""
    text = "isolated heptane droplet extinction"
    v_a = _deterministic_projection(text, dim=384)
    v_b = _deterministic_projection(text, dim=384)

    assert len(v_a) == 384
    assert v_a == v_b
    norm = math.sqrt(sum(x * x for x in v_a))
    assert math.isclose(norm, 1.0, abs_tol=1e-4)


# ==============================================================================
# 2. Scientific Entity Extraction Tests
# ==============================================================================

def test_entity_extractor_combustion_regimes():
    """Verifies entity extraction across all standard microgravity combustion regimes."""
    extractor = ScientificEntityExtractor()

    # Droplet combustion
    res1 = extractor.extract_entities("isolated heptane droplet extinction in microgravity")
    assert "droplet_combustion" in res1["combustion_regimes"]
    assert "n-Heptane" in res1["fuel_types"]

    # Laminar diffusion
    res2 = extractor.extract_entities("ACME coflow laminar diffusion methane flame")
    assert "laminar_diffusion" in res2["combustion_regimes"]
    assert "Methane" in res2["fuel_types"]

    # Solid flame spread
    res3 = extractor.extract_entities("BASS-II flame spread over PMMA solid fuel slabs")
    assert "solid_flame_spread" in res3["combustion_regimes"]
    assert "PMMA" in res3["fuel_types"]

    # Smoldering
    res4 = extractor.extract_entities("microgravity smoldering in porous polyurethane foam")
    assert "smoldering" in res4["combustion_regimes"]


def test_entity_extractor_measurements_and_facilities():
    """Verifies physical measurements and facility recognition."""
    extractor = ScientificEntityExtractor()
    text = "FLEX-2 droplet burning rate and extinction diameter in CIR chamber at 14.7 psi"
    entities = extractor.extract_entities(text)

    assert "CIR" in entities["facilities"]
    assert "Droplet Diameter" in entities["measurements"]
    assert "Burning Rate" in entities["measurements"]
    assert "Pressure" in entities["measurements"]

    flat = extractor.extract_flat(text)
    assert any("droplet" in e.lower() for e in flat)


def test_entity_extractor_non_domain_detection():
    """Verifies non-combustion text returns no combustion terms."""
    extractor = ScientificEntityExtractor()
    assert extractor.has_combustion_terms("What is the capital of Mars?") is False
    assert extractor.has_combustion_terms("Stock price prediction using Bitcoin blockchain") is False


# ==============================================================================
# 3. Hybrid Retriever & RRF Tests
# ==============================================================================

def test_hybrid_retriever_ranks_benchmark_investigations():
    """Verifies BM25 + dense vector similarity with RRF k=60 retrieves correct top records."""
    retriever = HybridRetriever()

    # FLEX-2 droplet test
    res_droplet = retriever.retrieve("What are the droplet extinction dynamics of n-heptane in microgravity?")
    assert len(res_droplet) >= 1
    assert res_droplet[0]["slug"] == "flex-2-heptane-droplet"
    assert res_droplet[0]["relevance_score"] >= 0.70
    assert "rrf_score" in res_droplet[0]

    # ACME diffusion flame test
    res_diffusion = retriever.retrieve("Explain soot formation in ACME laminar diffusion methane flames")
    assert len(res_diffusion) >= 1
    assert res_diffusion[0]["slug"] == "acme-cld-flame"
    assert res_diffusion[0]["relevance_score"] >= 0.70

    # BASS-II solid slab test
    res_solid = retriever.retrieve("What did the BASS-II investigation discover regarding PMMA flame spread?")
    assert len(res_solid) >= 1
    assert res_solid[0]["slug"] == "bass-ii-solid-slab"
    assert res_solid[0]["relevance_score"] >= 0.70


def test_hybrid_retriever_metadata_filtering():
    """Verifies retrieval filtering by combustion regime and fuel type."""
    retriever = HybridRetriever()
    filtered = retriever.retrieve(
        "combustion experiments",
        filters={"regime": "solid_flame_spread"},
    )
    assert len(filtered) >= 1
    for doc in filtered:
        assert doc["combustion_regime"] == "solid_flame_spread"


# ==============================================================================
# 4. Abstention Engine Tests
# ==============================================================================

def test_abstention_on_out_of_domain_queries():
    """Verifies that out-of-domain queries immediately trigger explicit abstention."""
    engine = AbstentionEngine()

    queries = [
        "What is the capital of Mars?",
        "How to bake a chocolate soufflé at high altitude?",
        "Quantum entanglement speeds in warp bubble drives",
        "Stock price forecasting using Bitcoin blockchain hashes",
        "Dark matter condensation in interstellar travel",
    ]

    for q in queries:
        eval_res = engine.evaluate_pre_retrieval(q, has_combustion_entities=False)
        assert eval_res is not None, f"Failed to abstain on '{q}'"
        assert eval_res.abstention_flag is True
        assert eval_res.confidence_score < 0.30
        assert "abstention" in eval_res.answer.lower() or "not correspond" in eval_res.answer.lower()


def test_abstention_on_mixed_speculative_query():
    """Verifies query containing combustion terms plus sci-fi warp drive triggers abstention (< 0.50)."""
    engine = AbstentionEngine()
    q = "Explain methane laminar diffusion flame dynamics in warp drive engines"
    eval_res = engine.evaluate_pre_retrieval(q, has_combustion_entities=True)
    assert eval_res is not None
    assert eval_res.abstention_flag is True
    assert eval_res.confidence_score < 0.50


# ==============================================================================
# 5. Citation Engine Tests
# ==============================================================================

def test_citation_engine_validates_official_nasa_urls():
    """Verifies citation engine only accepts authentic NASA NTRS and PSI source URLs."""
    citation_engine = CitationEngine()

    assert citation_engine.is_valid_nasa_url("https://ntrs.nasa.gov/citations/20140011032") is True
    assert citation_engine.is_valid_nasa_url("https://psi.nasa.gov/investigations/flex") is True
    assert citation_engine.is_valid_nasa_url("https://malicious.org/fake-nasa") is False
    assert citation_engine.is_valid_nasa_url("http://insecure-ntrs.nasa.gov/") is False


def test_citation_engine_discards_invalid_records():
    """Verifies citations missing required fields or having invalid URLs are discarded."""
    citation_engine = CitationEngine()

    candidate_docs = [
        {
            "slug": "flex-2-heptane-droplet",
            "title": "FLEX-2 Heptane Droplet Combustion in Microgravity",
            "nasa_source_url": "https://ntrs.nasa.gov/citations/20140011032",
            "relevance_score": 0.94,
        },
        {
            "slug": "fake-investigation",
            "title": "Fabricated Experiment",
            "nasa_source_url": "https://fake-site.com/fake",
            "relevance_score": 0.85,
        },
    ]

    citations = citation_engine.build_citations(candidate_docs)
    assert len(citations) == 1
    assert citations[0]["investigation_id"] == "flex-2-heptane-droplet"
    assert citations[0]["nasa_source_url"].startswith("https://ntrs.nasa.gov/")


# ==============================================================================
# 6. Full 7-Stage Pipeline End-to-End Tests
# ==============================================================================

def test_si_pipeline_e2e_grounded_droplet_query():
    """Verifies end-to-end pipeline execution on authentic FLEX-2 droplet inquiry."""
    pipeline = ScientificIntelligencePipeline()
    response = pipeline.process_query("What are the droplet extinction characteristics of n-heptane in microgravity?")

    assert response["abstention_flag"] is False
    assert response["confidence_score"] >= 0.70
    assert len(response["citations"]) >= 1
    assert response["citations"][0]["investigation_id"] == "flex-2-heptane-droplet"
    assert response["citations"][0]["nasa_source_url"].startswith("https://ntrs.nasa.gov/")
    assert len(response["explainability"]["matched_entities"]) > 0
    assert response["explainability"]["retrieval_method"] == "hybrid_rrf_bm25_vector"
    assert response["explainability"]["abstention_reason"] is None


def test_si_pipeline_e2e_out_of_domain_abstention():
    """Verifies end-to-end pipeline enforces zero citations on out-of-domain abstention."""
    pipeline = ScientificIntelligencePipeline()
    response = pipeline.process_query("What is the capital of Mars?")

    assert response["abstention_flag"] is True
    assert response["confidence_score"] < 0.30
    assert len(response["citations"]) == 0
    assert "abstention" in response["answer"].lower() or "not correspond" in response["answer"].lower()
    assert response["explainability"]["abstention_reason"] is not None


# ==============================================================================
# 7. SIService Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_si_service_rejects_empty_query():
    """Verifies SIService raises HTTP 422 on empty or whitespace query."""
    with pytest.raises(HTTPException) as exc_info:
        await SIService.process_query(session=None, query_str="   ")
    assert exc_info.value.status_code == 422
