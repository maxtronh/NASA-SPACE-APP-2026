from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.investigation_service import InvestigationService


class ComparisonService:

    @staticmethod
    async def compare(
        session: AsyncSession,
        investigation_ids: list[str],
    ) -> dict[str, Any]:
        """Compares two or more investigations side-by-side with scientific condition equivalence assessment."""
        if len(investigation_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Comparison requires at least 2 investigation IDs",
            )

        records = []
        for i_id in investigation_ids:
            try:
                detail = await InvestigationService.get_investigation_detail(session, i_id)
                records.append(detail)
            except HTTPException as e:
                if e.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Investigation '{i_id}' not found for comparison",
                    )
                raise

        # Condition equivalence evaluation
        gravities = {r["investigation"]["gravity_level"] for r in records}
        regimes = {r["investigation"]["combustion_regime"] for r in records}
        fuels = {r["investigation"]["fuel_type"] for r in records}

        reasons = []
        is_equivalent = True

        if len(gravities) > 1:
            is_equivalent = False
            reasons.append(f"Gravitational regime mismatch: {sorted(gravities)}")
        if len(regimes) > 1:
            is_equivalent = False
            reasons.append(f"Combustion regime mismatch: {sorted(regimes)}")
        if len(fuels) > 1:
            reasons.append(f"Different fuel types: {sorted(fuels)}")

        # Comparison matrix
        grid = {}
        for r in records:
            slug = r["investigation"]["slug"]
            si_m = r["provenance"]["si_measurements"]
            grid[slug] = {
                "title": r["investigation"]["title"],
                "regime": r["investigation"]["combustion_regime"],
                "gravity": r["investigation"]["gravity_level"],
                "fuel": r["investigation"]["fuel_type"],
                "si_measurements": si_m,
            }

        return {
            "investigation_ids": investigation_ids,
            "equivalence_assessment": {
                "equivalent": is_equivalent,
                "reasons": reasons if reasons else ["Research conditions are directly comparable"],
            },
            "comparison_grid": grid,
        }
