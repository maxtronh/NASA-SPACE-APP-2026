"""Scientific abstention and calibrated confidence engine for NASA Microgravity Combustion SI.

Evaluates natural language queries and retrieved evidence to determine whether
the system has sufficient empirical evidence to formulate a scientific answer,
triggering explicit abstention with zero hallucinated citations when evidence is lacking
or when questions are out-of-domain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Patterns indicating speculative or strictly out-of-domain topics
SPECULATIVE_OR_OUT_OF_DOMAIN_PATTERNS = [
    # Speculative Sci-Fi / Non-combustion physics
    r"\bwarp(?:\s+drive|\s+bubble|\s+core)?\b",
    r"\bquantum(?:\s+entanglement|\s+computing|\s+tunneling)?\b",
    r"\bdark\s+matter\b",
    r"\bwormhole\b",
    r"\btachyon\b",
    r"\bsubspace\b",
    r"\bhyperdrive\b",
    r"\bantimatter\s+reactor\b",
    r"\binterstellar\s+travel\b",
    # Financial / Crypto
    r"\bbitcoin\b",
    r"\bblockchain\b",
    r"\bcrypto(?:currency)?\b",
    r"\bstock(?:\s+price)?\b",
    r"\bforecasting\s+using\b",
    r"\bethereum\b",
    r"\btrading\b",
    r"\bnft\b",
    # Culinary / Food
    r"\bchocolate\b",
    r"\bsouffl[eé]\b",
    r"\bcake\b",
    r"\bbake\b",
    r"\bbaking\b",
    r"\brecipe\b",
    r"\bcooking\b",
    r"\bpastry\b",
    # General non-scientific trivia / geography
    r"\bcapital\s+of\b",
    r"\bpresident\s+of\b",
    r"\bwho\s+is\b",
    r"\bweather\s+in\b",
]

COMPILED_OUT_OF_DOMAIN = [re.compile(p, re.IGNORECASE) for p in SPECULATIVE_OR_OUT_OF_DOMAIN_PATTERNS]


@dataclass
class AbstentionEvaluation:
    """Outcome of domain and confidence evaluation."""

    abstention_flag: bool
    confidence_score: float
    abstention_reason: str | None
    answer: str | None


class AbstentionEngine:
    """Evaluates query validity and calibrates scientific confidence to enforce zero-hallucination abstention."""

    ABSTENTION_CONFIDENCE_THRESHOLD = 0.50
    OUT_OF_DOMAIN_CONFIDENCE = 0.12
    MIXED_QUERY_CONFIDENCE = 0.28

    CANONICAL_ABSTENTION_ANSWER = (
        "Abstention: The query does not correspond to indexed NASA microgravity "
        "combustion research evidence."
    )

    def __init__(self, threshold: float = ABSTENTION_CONFIDENCE_THRESHOLD):
        self.threshold = threshold

    def evaluate_pre_retrieval(
        self,
        query: str,
        has_combustion_entities: bool,
    ) -> AbstentionEvaluation | None:
        """Pre-retrieval check for obvious out-of-domain, adversarial, or speculative queries.

        Returns an AbstentionEvaluation if immediate abstention is required, or None to proceed.
        """
        clean = query.strip()
        if not clean:
            return AbstentionEvaluation(
                abstention_flag=True,
                confidence_score=0.0,
                abstention_reason="Empty query string.",
                answer=self.CANONICAL_ABSTENTION_ANSWER,
            )

        matched_speculative = [
            p.pattern for p in COMPILED_OUT_OF_DOMAIN if p.search(clean)
        ]

        # Case 1: Speculative / out-of-domain terms detected
        if matched_speculative:
            # Check if query also contains legitimate combustion terms (mixed query)
            if has_combustion_entities:
                return AbstentionEvaluation(
                    abstention_flag=True,
                    confidence_score=self.MIXED_QUERY_CONFIDENCE,
                    abstention_reason=(
                        "Query combines microgravity combustion terms with speculative or "
                        "out-of-domain concepts unsupported by authenticated empirical NASA data."
                    ),
                    answer=(
                        f"{self.CANONICAL_ABSTENTION_ANSWER} The query references speculative concepts "
                        "incompatible with empirical research archives."
                    ),
                )
            # Pure out-of-domain
            return AbstentionEvaluation(
                abstention_flag=True,
                confidence_score=self.OUT_OF_DOMAIN_CONFIDENCE,
                abstention_reason="Out-of-domain query not indexed in NASA PSI/NTRS records.",
                answer=self.CANONICAL_ABSTENTION_ANSWER,
            )

        # Case 2: Zero combustion entities matched and very short or non-domain
        if not has_combustion_entities:
            # Let retrieval run if there might be fuzzy match, but flag low baseline
            return None

        return None

    def calibrate_confidence(
        self,
        retrieval_relevance: float,
        entity_count: int,
        vector_similarity: float,
    ) -> float:
        """Calculates a calibrated confidence score bounded in [0.0, 1.0]."""
        # Weighted combination of RRF relevance, vector similarity, and entity grounding
        entity_bonus = min(0.15, entity_count * 0.05)
        raw_score = (0.50 * retrieval_relevance) + (0.35 * vector_similarity) + entity_bonus
        # High-relevance ceiling calibration for grounded answers
        if raw_score >= 0.50:
            calibrated = 0.70 + (raw_score - 0.50) * 0.50
            return round(float(min(0.96, calibrated)), 4)
        return round(float(max(0.05, raw_score)), 4)

    def evaluate_post_retrieval(
        self,
        query: str,
        retrieved_docs: list[Any],
        entity_count: int,
        top_relevance: float,
    ) -> AbstentionEvaluation:
        """Post-retrieval evidence check.

        If top relevance score is below threshold or no documents are retrieved,
        triggers explicit abstention.
        """
        if not retrieved_docs or top_relevance < 0.40 or (entity_count == 0 and top_relevance < 0.55):
            score = round(max(0.08, min(0.35, top_relevance * 0.6)), 2)
            return AbstentionEvaluation(
                abstention_flag=True,
                confidence_score=score,
                abstention_reason="Low semantic similarity to authenticated NASA PSI/NTRS records.",
                answer=self.CANONICAL_ABSTENTION_ANSWER,
            )

        # Calibrated in-domain score
        calibrated = self.calibrate_confidence(
            retrieval_relevance=top_relevance,
            entity_count=entity_count,
            vector_similarity=top_relevance,
        )

        if calibrated < self.threshold:
            return AbstentionEvaluation(
                abstention_flag=True,
                confidence_score=calibrated,
                abstention_reason=f"Calibrated confidence {calibrated} below threshold {self.threshold}.",
                answer=self.CANONICAL_ABSTENTION_ANSWER,
            )

        return AbstentionEvaluation(
            abstention_flag=False,
            confidence_score=calibrated,
            abstention_reason=None,
            answer=None,
        )
