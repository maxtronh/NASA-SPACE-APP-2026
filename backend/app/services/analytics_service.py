import collections
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.investigation import Investigation
from backend.app.models.measurement import Measurement
from backend.app.models.test_run import TestRun


class AnalyticsService:

    @staticmethod
    async def get_corpus_analytics(session: AsyncSession) -> dict[str, Any]:
        """Calculates global corpus metrics, regime distributions, and missing data matrix using batch queries."""
        # 1. Total investigations and regime distribution
        query = select(Investigation)
        result = await session.execute(query)
        investigations = result.scalars().all()

        total = len(investigations)
        regime_counts: dict[str, int] = {}
        for inv in investigations:
            reg = inv.combustion_regime
            regime_counts[reg] = regime_counts.get(reg, 0) + 1

        # 2. Aggregate test run & measurement counts
        total_runs_res = await session.execute(select(func.count(TestRun.id)))
        total_runs = total_runs_res.scalar_one() or 0

        total_meas_res = await session.execute(select(func.count(Measurement.id)))
        total_measurements = total_meas_res.scalar_one() or 0

        # 3. Single-batch load of all measurements across all investigations
        meas_res = await session.execute(select(Measurement))
        all_measurements = meas_res.scalars().all()

        suffix_map = {
            "initial_droplet_diameter": "m",
            "soot_volume_fraction": "dimensionless",
            "radiative_flux": "w_m2",
            "chamber_pressure": "pa",
            "spread_rate": "m_s",
            "fuel_flow_rate": "m3_s",
        }

        meas_by_inv: dict[Any, dict[str, Any]] = collections.defaultdict(dict)
        for m in all_measurements:
            unit_clean = (
                m.unit_si.replace("/", "_").replace("^", "")
                if m.unit_si
                else suffix_map.get(m.metric_name, "si")
            )
            key = f"{m.metric_name}_{unit_clean}"
            meas_by_inv[m.investigation_id][key] = m.value_si

        # 4. Fallback check from TestRun si_normalized_parameters
        tr_res = await session.execute(select(TestRun))
        for tr in tr_res.scalars().all():
            if tr.investigation_id not in meas_by_inv or not meas_by_inv[tr.investigation_id]:
                if tr.si_normalized_parameters:
                    meas_by_inv[tr.investigation_id].update(tr.si_normalized_parameters)

        all_keys = set()
        for si_dict in meas_by_inv.values():
            all_keys.update(si_dict.keys())

        missing_matrix: dict[str, dict[str, Any]] = {}
        for k in sorted(all_keys):
            present = sum(
                1 for inv in investigations if meas_by_inv.get(inv.id, {}).get(k) is not None
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
