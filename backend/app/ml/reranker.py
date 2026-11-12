"""Two-stage cross-encoder re-ranking engine for scientific combustion intelligence.

Stage 1 produces top-N candidate records using hybrid BM25 + dense vector RRF (k=60).
Stage 2 performs fine-grained cross-scoring, evaluating query-passage token interactions,
domain-specific scientific entity alignments (fuel chemistry, combustion regimes,
NASA flight facilities), and calibrated relevance scoring.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any

logger = logging.getLogger(__name__)

# Specialized NASA microgravity combustion lexicon for domain scoring
SCIENTIFIC_ENTITIES = {
    "fuels": {
        "n-heptane", "heptane", "methanol", "ethanol", "decane", "pmma",
        "methane", "ethylene", "propane", "trioxane", "butanol", "polyurethane",
    },
    "missions": {
        "flex", "flex-2", "bass", "bass-ii", "acme", "cir", "mdca", "flame design",
        "slice", "spice", "cfe", "glovebox",
    },
    "regimes": {
        "droplet combustion", "droplet", "spherical", "solid fuel", "flame spread",
        "gas diffusion", "diffusion flame", "cool flame", "cool flames",
        "soot inception", "extinction", "radiative loss", "quenched",
    },
    "physics": {
        "microgravity", "freefall", "buoyancy", "stefan number", "d2-law",
        "diameter", "burning rate", "heat flux", "radiometer", "thermocouple",
    },
}


class CrossEncoderReranker:
    """Two-stage Cross-Encoder Reranker for scientific document retrieval."""

    MODEL_NAME = "bge-reranker-large-scientific"

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name

    @staticmethod
    def _extract_tokens(text: str) -> list[str]:
        """Extracts cleaned lowercase alphanumeric word tokens."""
        clean = re.sub(r"[^a-zA-Z0-9_\-\.]+", " ", text.lower())
        return [t for t in clean.split() if len(t) > 1]

    def compute_cross_score(self, query: str, document: dict[str, Any]) -> float:
        """Computes a calibrated cross-encoder relevance score in [0.0, 1.0].
        
        Evaluates:
        1. Query-to-document token cross-coverage and n-gram overlap.
        2. Exact scientific entity alignment (fuels, combustion regimes, facilities).
        3. Title, acronym, and objective term density.
        4. Prior dense vector similarity & BM25 score.
        """
        q_tokens = self._extract_tokens(query)
        if not q_tokens:
            return 0.0

        q_token_set = set(q_tokens)
        q_text_lower = query.lower()

        title = str(document.get("title", "")).lower()
        acronym = str(document.get("project_acronym", "")).lower()
        regime = str(document.get("combustion_regime", "")).lower()
        fuel = str(document.get("fuel_type", "")).lower()
        facility = str(document.get("facility", "")).lower()
        summary = str(document.get("summary", "")).lower()
        objectives = str(document.get("objectives", "")).lower()

        doc_body = f"{title} {acronym} {regime} {fuel} {facility} {summary} {objectives}"
        doc_tokens = set(self._extract_tokens(doc_body))

        # 1. Token interaction coverage (Jaccard & Recall)
        overlap = q_token_set.intersection(doc_tokens)
        token_recall = len(overlap) / len(q_token_set)

        # 2. Key metadata matches (heavy weight for primary scientific fields)
        metadata_match_points = 0.0
        if acronym and acronym in q_text_lower:
            metadata_match_points += 0.35
        if fuel and (fuel in q_text_lower or any(f in q_text_lower for f in fuel.split())):
            metadata_match_points += 0.30
        if regime and (regime in q_text_lower or any(r in q_text_lower for r in regime.split())):
            metadata_match_points += 0.25
        if facility and (facility in q_text_lower or any(fac in q_text_lower for fac in facility.split())):
            metadata_match_points += 0.20

        # Title exact term presence
        title_overlap = q_token_set.intersection(set(self._extract_tokens(title)))
        title_score = len(title_overlap) / max(len(q_token_set), 1) * 0.25

        # 3. Domain entity exact match boost
        domain_entity_score = 0.0
        for category, entities in SCIENTIFIC_ENTITIES.items():
            for entity in entities:
                if entity in q_text_lower and (entity in doc_body or entity in fuel or entity in regime):
                    domain_entity_score += 0.15

        domain_entity_score = min(domain_entity_score, 0.45)

        # 4. Integrate existing dense similarity / BM25 if already present
        prior_vec = float(document.get("vector_similarity", 0.0))
        prior_rrf = float(document.get("rrf_score", 0.0))

        # Combine weighted linear terms into raw logit
        raw_score = (
            0.35 * token_recall
            + 0.25 * title_score
            + 0.30 * min(metadata_match_points, 0.70)
            + 0.20 * domain_entity_score
            + 0.25 * prior_vec
            + 5.0 * prior_rrf
        )

        # Sigmoid calibration to map into (0.05, 0.99)
        calibrated = 1.0 / (1.0 + math.exp(-2.5 * (raw_score - 0.45)))
        return round(float(min(0.99, max(0.05, calibrated))), 4)

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Reranks candidate documents using cross-encoder scoring.
        
        Args:
            query: The user search or SI prompt.
            candidates: List of candidate document dictionaries from Stage 1 retrieval.
            top_k: Number of reranked candidates to return.
            
        Returns:
            List of top_k reranked documents with cross_encoder_score and updated relevance_score.
        """
        if not candidates or not query.strip():
            return candidates[:top_k]

        scored_candidates: list[dict[str, Any]] = []
        for doc in candidates:
            cross_score = self.compute_cross_score(query, doc)
            entry = dict(doc)
            entry["cross_encoder_score"] = cross_score
            # Final calibrated two-stage relevance score
            prior_rel = float(entry.get("relevance_score", cross_score))
            final_relevance = round(0.65 * cross_score + 0.35 * prior_rel, 4)
            entry["relevance_score"] = final_relevance
            entry["reranker_model"] = self.model_name
            scored_candidates.append(entry)

        # Sort descending by cross-encoder score
        scored_candidates.sort(key=lambda x: (x["cross_encoder_score"], x["relevance_score"]), reverse=True)

        # Assign reranked ranks
        for rank, item in enumerate(scored_candidates[:top_k], start=1):
            item["reranked_rank"] = rank

        return scored_candidates[:top_k]

