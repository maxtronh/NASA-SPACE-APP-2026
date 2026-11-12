"""Tests for two-stage CrossEncoderReranker and hybrid retrieval re-ranking."""

import pytest

from backend.app.ml.reranker import CrossEncoderReranker
from backend.app.ml.retriever import HybridRetriever


def test_cross_encoder_reranker_initialization():
    reranker = CrossEncoderReranker()
    assert reranker.model_name == "bge-reranker-large-scientific"


def test_cross_encoder_compute_cross_score_relevance():
    reranker = CrossEncoderReranker()
    doc_flex = {
        "title": "Flame Extinction Experiment (FLEX) Droplet Combustion",
        "project_acronym": "FLEX",
        "combustion_regime": "droplet combustion",
        "fuel_type": "n-heptane",
        "facility": "Combustion Integrated Rack (CIR)",
        "summary": "Investigates isolated spherical droplet combustion in microgravity.",
        "objectives": "Determine burning rate constant and cool flame extinction.",
        "vector_similarity": 0.85,
        "rrf_score": 0.03,
    }

    doc_acme = {
        "title": "Advanced Combustion via Microgravity Experiments (ACME)",
        "project_acronym": "ACME",
        "combustion_regime": "gas diffusion flame",
        "fuel_type": "methane",
        "facility": "CIR",
        "summary": "Studies laminar methane gas diffusion flames and soot inception.",
        "objectives": "Evaluate soot limits and radiant fraction.",
        "vector_similarity": 0.35,
        "rrf_score": 0.01,
    }

    query_droplet = "What is the droplet burning rate and cool flame behavior of n-heptane?"
    score_flex = reranker.compute_cross_score(query_droplet, doc_flex)
    score_acme = reranker.compute_cross_score(query_droplet, doc_acme)

    assert 0.0 < score_flex <= 1.0
    assert 0.0 < score_acme <= 1.0
    # FLEX droplet record should score substantially higher than ACME gas diffusion record for droplet query
    assert score_flex > score_acme


def test_cross_encoder_rerank_sorting():
    reranker = CrossEncoderReranker()
    candidates = [
        {
            "slug": "acme-diffusion",
            "title": "ACME Diffusion Flame",
            "project_acronym": "ACME",
            "combustion_regime": "gas diffusion flame",
            "fuel_type": "methane",
            "relevance_score": 0.50,
        },
        {
            "slug": "flex-droplet",
            "title": "FLEX Droplet Burning",
            "project_acronym": "FLEX",
            "combustion_regime": "droplet combustion",
            "fuel_type": "n-heptane",
            "relevance_score": 0.45,
        },
    ]

    reranked = reranker.rerank(
        query="FLEX n-heptane droplet burning",
        candidates=candidates,
        top_k=2,
    )

    assert len(reranked) == 2
    assert reranked[0]["slug"] == "flex-droplet"
    assert reranked[0]["reranked_rank"] == 1
    assert "cross_encoder_score" in reranked[0]
    assert "reranker_model" in reranked[0]


def test_hybrid_retriever_with_reranking():
    retriever = HybridRetriever()
    results_reranked = retriever.retrieve(
        query="droplet burning rate n-heptane FLEX",
        top_k=3,
        rerank=True,
    )
    assert len(results_reranked) > 0
    top_doc = results_reranked[0]
    assert "cross_encoder_score" in top_doc
    assert "reranked_rank" in top_doc
    assert top_doc.get("project_acronym") == "FLEX" or "droplet" in str(top_doc.get("title", "")).lower()


def test_hybrid_retriever_without_reranking():
    retriever = HybridRetriever()
    results_plain = retriever.retrieve(
        query="droplet burning rate n-heptane",
        top_k=2,
        rerank=False,
    )
    assert len(results_plain) > 0
    # Should not have cross_encoder_score when rerank is False
    assert "cross_encoder_score" not in results_plain[0]

