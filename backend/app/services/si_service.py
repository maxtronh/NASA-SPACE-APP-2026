"""Scientific Intelligence (SI) service orchestrating domain extraction, hybrid retrieval, and citation verification."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ml.pipeline import ScientificIntelligencePipeline
from backend.app.services.investigation_service import InvestigationService

logger = logging.getLogger(__name__)

_si_pipeline: ScientificIntelligencePipeline | None = None


def get_si_pipeline() -> ScientificIntelligencePipeline:
    """Returns the singleton Scientific Intelligence Pipeline instance."""
    global _si_pipeline
    if _si_pipeline is None:
        logger.info("Initializing ScientificIntelligencePipeline singleton...")
        _si_pipeline = ScientificIntelligencePipeline()
    return _si_pipeline


class SIService:

    @staticmethod
    async def process_query(
        session: AsyncSession,
        query_str: str,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Processes scientific intelligence query with domain extraction, hybrid retrieval, and citation verification."""
        q = query_str.strip()
        if not q:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Query string cannot be empty",
            )

        pipeline = get_si_pipeline()
        response = pipeline.process_query(query=query_str, filters=filters)

        # Enhance citation provenance from database when available
        if not response.get("abstention_flag", False) and response.get("citations"):
            top_citation = response["citations"][0]
            target_slug = top_citation.get("investigation_id")
            if target_slug:
                try:
                    detail = await InvestigationService.get_investigation_detail(session, target_slug)
                    inv = detail.get("investigation")
                    if inv:
                        top_citation["title"] = inv.get("title", top_citation["title"])
                        top_citation["nasa_source_url"] = inv.get("nasa_source_url", top_citation["nasa_source_url"])
                except (HTTPException, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
                    logger.debug(f"Database citation enrichment skipped: {exc}")

        return response
