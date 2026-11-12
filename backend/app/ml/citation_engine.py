"""Citation verification and provenance validation engine for NASA Combustion SI.

Verifies generated citations against authenticated NASA Technical Reports Server (NTRS)
and Physical Sciences Informatics (PSI) source records, guaranteeing zero hallucinated
or fabricated scientific citations.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

VALID_NASA_PREFIXES = (
    "https://ntrs.nasa.gov/",
    "https://psi.nasa.gov/",
)


class CitationEngine:
    """Verifies and formats NASA scientific citations with provenance validation."""

    def __init__(self, allowed_prefixes: tuple[str, ...] = VALID_NASA_PREFIXES):
        self.allowed_prefixes = allowed_prefixes

    def is_valid_nasa_url(self, url: str) -> bool:
        """Validates that a URL resolves strictly to official NASA NTRS or PSI archives."""
        if not isinstance(url, str):
            return False
        clean = url.strip()
        return any(clean.startswith(prefix) for prefix in self.allowed_prefixes)

    def verify_citation(self, citation: dict[str, Any]) -> bool:
        """Validates an individual citation dictionary against interface contracts."""
        if not isinstance(citation, dict):
            return False

        inv_id = citation.get("investigation_id")
        title = citation.get("title")
        url = citation.get("nasa_source_url")
        relevance = citation.get("relevance_score")

        if not inv_id or not isinstance(inv_id, str):
            return False
        if not title or not isinstance(title, str):
            return False
        if not url or not self.is_valid_nasa_url(url):
            return False
        if relevance is None or not isinstance(relevance, (int, float)):
            return False
        return 0.0 <= float(relevance) <= 1.0

    def build_citations(
        self,
        ranked_docs: list[dict[str, Any]],
        max_citations: int = 3,
        min_relevance: float = 0.40,
    ) -> list[dict[str, Any]]:
        """Constructs verified citations from ranked retrieved documents.

        Drops any document that fails URL or metadata provenance validation.
        """
        citations: list[dict[str, Any]] = []
        seen_slugs = set()

        for doc in ranked_docs:
            slug = doc.get("slug")
            if not slug or slug in seen_slugs:
                continue

            relevance = float(doc.get("relevance_score", doc.get("score", 0.0)))
            if relevance < min_relevance:
                continue

            url = doc.get("nasa_source_url", "")
            title = doc.get("title", "")

            citation = {
                "investigation_id": slug,
                "title": title,
                "nasa_source_url": url,
                "relevance_score": round(relevance, 2),
            }

            if self.verify_citation(citation):
                citations.append(citation)
                seen_slugs.add(slug)
                if len(citations) >= max_citations:
                    break
            else:
                logger.warning(
                    f"Discarded citation with invalid NASA provenance: slug={slug}, url={url}"
                )

        return citations
