from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.investigation import Investigation
from backend.app.models.measurement import Measurement
from backend.app.models.test_run import TestRun
from backend.app.services.investigation_service import InvestigationService


class AnalyticsService:

    @staticmethod
    async def get_corpus_analytics(session: AsyncSession) -> dict[str, Any]:
        """Calculates global corpus metrics, regime distributions, and missing data matrix."""
        query = select(Investigation)
        result = await session.execute(query)
        investigations = result.scalars().all()

        total = len(investigations)
        regime_counts: dict[str, int] = {}

        # Aggregate counts
        total_runs_res = await session.execute(select(func.count(TestRun.id)))
        total_runs = total_runs_res.scalar_one() or 0

        total_meas_res = await session.execute(select(func.count(Measurement.id)))
        total_measurements = total_meas_res.scalar_one() or 0

        # Fetch detail for each to gather complete measurement metrics
        all_details = []
        for inv in investigations:
            reg = inv.combustion_regime
            regime_counts[reg] = regime_counts.get(reg, 0) + 1
            detail = await InvestigationService.get_investigation_detail(session, inv.slug)
            all_details.append(detail)

        all_keys = set()
        for item in all_details:
            all_keys.update(item["provenance"]["si_measurements"].keys())

        missing_matrix: dict[str, dict[str, Any]] = {}
        for k in sorted(all_keys):
            present = sum(
                1 for item in all_details if item["provenance"]["si_measurements"].get(k) is not None
            )
            missing = total - present
            pct = round((present / total) * 100.0, 1) if total > 0 else 0.0
            missing_matrix[k] = {
                "present_count": present,
                "missing_count": missing,
                "completeness_pct": pct,
            }

        return {
            "total_investigations": total,
            "total_test_runs": total_runs,
            "total_measurements": total_measurements,
            "combustion_regimes": regime_counts,
            "missing_data_matrix": missing_matrix,
        }
