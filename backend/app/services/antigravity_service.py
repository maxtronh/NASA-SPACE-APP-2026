"""Antigravity Comparison Service for multi-regime gravitational combustion analysis.

Supports comparisons across microgravity (~10^-6 g), lunar (0.16g), Mars (0.38g),
normal gravity (1.0g), and hypergravity (2g, 5g) regimes.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.gravity import (
    calculate_buoyancy_parameter,
    classify_convection_regime,
    classify_flame_geometry,
    classify_soot_behavior,
    generate_buoyancy_warning,
    get_gravity_regime_category,
    normalize_gravity_level,
)
from backend.app.services.comparison_service import ComparisonService
from backend.app.services.investigation_service import InvestigationService

logger = logging.getLogger(__name__)


class AntigravityComparisonService:
    """Provides multi-gravity comparison and equivalence analysis across gravity spectrums."""

    @staticmethod
    async def compare_with_gravity_regimes(
        session: AsyncSession,
        investigation_ids: list[str],
        gravity_regimes: list[str] | None = None,
        include_equivalence_matrix: bool = True,
    ) -> dict[str, Any]:
        """Compares investigations across arbitrary gravitational levels with convection profiling."""
        if not investigation_ids or len(investigation_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Antigravity comparison requires at least 2 investigation IDs",
            )

        if len(investigation_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Antigravity comparison supports at most 5 investigation IDs concurrently",
            )

        # Retrieve investigation details
        records: list[dict[str, Any]] = []
        for i_id in investigation_ids:
            try:
                detail = await InvestigationService.get_investigation_detail(session, i_id)
                records.append(detail)
            except HTTPException as exc:
                if exc.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Investigation '{i_id}' not found for antigravity comparison",
                    )
                raise

        # Filter by gravity regimes if specified
        if gravity_regimes:
            normalized_regime_filters = {
                normalize_gravity_level(r) for r in gravity_regimes if r
            }
            filtered_records = [
                r for r in records
                if normalize_gravity_level(r["investigation"]["gravity_level"]) in normalized_regime_filters
            ]
            if len(filtered_records) >= 2:
                records = filtered_records

        # Build gravity regime profiles and matrix
        gravity_matrix: dict[str, dict[str, Any]] = {}
        distinct_gravity_levels: list[str] = []

        for r in records:
            inv = r["investigation"]
            slug = inv["slug"]
            g_raw = inv["gravity_level"]
            canonical_g = normalize_gravity_level(g_raw)

            if canonical_g not in distinct_gravity_levels:
                distinct_gravity_levels.append(canonical_g)

            gravity_matrix[slug] = {
                "gravity_level": canonical_g,
                "category": get_gravity_regime_category(canonical_g),
                "buoyancy_parameter": calculate_buoyancy_parameter(canonical_g),
                "convection_regime": classify_convection_regime(canonical_g),
                "flame_geometry": classify_flame_geometry(canonical_g),
                "soot_behavior": classify_soot_behavior(canonical_g),
            }

        # Equivalence assessment and buoyancy warning
        buoyancy_warning = generate_buoyancy_warning(distinct_gravity_levels)

        # Baseline comparison
        base_comparison = await ComparisonService.compare(
            session=session,
            investigation_ids=[r["investigation"]["slug"] for r in records],
        )

        equivalence = base_comparison["equivalence_assessment"]
        if buoyancy_warning:
            equivalence["buoyancy_warning"] = buoyancy_warning
            if "Gravitational regime mismatch" not in " ".join(equivalence["reasons"]):
                equivalence["reasons"].append(f"Gravitational regime mismatch: {sorted(distinct_gravity_levels)}")
                equivalence["equivalent"] = False

        return {
            "investigation_ids": [r["investigation"]["slug"] for r in records],
            "gravity_regimes_compared": distinct_gravity_levels,
            "equivalence_assessment": equivalence,
            "gravity_matrix": gravity_matrix,
            "comparison_grid": base_comparison["comparison_grid"],
            "buoyancy_warning": buoyancy_warning,
        }
