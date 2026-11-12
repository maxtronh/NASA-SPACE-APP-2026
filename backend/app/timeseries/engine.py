"""
In-process DuckDB Timeseries Query and Decimation Engine.
Executes vectorized SIMD OLAP queries over Snappy-compressed Parquet files
with bucketed decimation, column projection, and strict non-zero NULL preservation.
"""

from pathlib import Path
from typing import Any

import duckdb
from backend.app.timeseries.schemas import NUMERIC_SENSOR_METRICS


class DuckDBTimeseriesEngine:
    """Vectorized in-process query engine for sensor timeseries telemetry using DuckDB."""

    def __init__(self, timeseries_dir: Path | str | None = None):
        if timeseries_dir is None:
            self.timeseries_dir = Path("data/timeseries")
        else:
            self.timeseries_dir = Path(timeseries_dir)
        self.conn = duckdb.connect(database=":memory:")

    def get_run_files(self, investigation_slug: str, run_identifier: str | None = None) -> list[Path]:
        """Resolves target Parquet files for an investigation and optional run identifier."""
        slug_dir = self.timeseries_dir / investigation_slug.strip().lower()
        if not slug_dir.exists():
            return []

        if run_identifier:
            target = slug_dir / f"{run_identifier.strip()}.parquet"
            return [target] if target.is_file() else []

        # Return all parquet files for this slug, sorted
        return sorted(slug_dir.glob("*.parquet"))

    def resolve_default_metric(self, investigation_slug: str) -> str:
        """Selects the standard physical metric channel for an investigation type."""
        slug = investigation_slug.lower()
        if "droplet" in slug or "flex" in slug:
            return "droplet_diameter_squared_mm2"
        if "solid" in slug or "slab" in slug or "bass" in slug:
            return "flame_spread_rate_mm_s"
        if "cld" in slug or "acme" in slug:
            return "soot_volume_fraction"
        return "radiant_flux_w"

    def query_timeseries(
        self,
        investigation_slug: str,
        run_identifier: str | None = None,
        metric: str | None = None,
        downsample_points: int | None = 500,
        start_time: float | None = None,
        end_time: float | None = None,
        decimation_method: str = "ntile",
    ) -> dict[str, Any]:
        """
        Queries timeseries telemetry with column projection, time range filters,
        bucketed downsampling (via SQL NTILE or window decimation), and window statistics.

        Strictly preserves NULL values and genuine 0.0 readings.
        """
        slug = investigation_slug.strip().lower()
        files = self.get_run_files(slug, run_identifier)

        if not files:
            # Gracefully handle when no parquet files are found
            chosen_metric = metric or self.resolve_default_metric(slug)
            return {
                "investigation_id": slug,
                "run_id": run_identifier,
                "metric": chosen_metric,
                "sampling_rate_hz": 30.0,
                "total_points": 0,
                "downsampled": False,
                "channels": NUMERIC_SENSOR_METRICS,
                "telemetry": [],
                "statistics": {
                    "min": None,
                    "max": None,
                    "mean": None,
                    "null_count": 0,
                    "valid_count": 0,
                },
            }

        # Target the primary run file
        target_file = files[0]
        actual_run_id = target_file.stem
        file_path_str = target_file.as_posix()

        # Validate metric name against allowed channels to prevent SQL injection
        if metric:
            metric_clean = metric.strip()
            if metric_clean not in NUMERIC_SENSOR_METRICS and not metric_clean.replace("_", "").isalnum():
                raise ValueError(f"Invalid metric channel name: '{metric}'")
            query_metric = metric_clean
        else:
            query_metric = self.resolve_default_metric(slug)

        # Build filter conditions
        where_clauses = ["1=1"]
        params: list[Any] = [file_path_str]

        if start_time is not None:
            where_clauses.append("time_seconds >= ?")
            params.append(float(start_time))
        if end_time is not None:
            where_clauses.append("time_seconds <= ?")
            params.append(float(end_time))

        filter_sql = " AND ".join(where_clauses)

        # 1. Compute summary statistics over the metric
        stats_sql = f"""
            SELECT
                COUNT(*) AS total_points,
                COUNT({query_metric}) AS valid_count,
                COUNT(*) - COUNT({query_metric}) AS null_count,
                MIN({query_metric}) AS min_val,
                MAX({query_metric}) AS max_val,
                AVG({query_metric}) AS mean_val,
                MIN(time_seconds) AS min_time,
                MAX(time_seconds) AS max_time
            FROM read_parquet(?)
            WHERE {filter_sql}
        """

        stats_row = self.conn.execute(stats_sql, params).fetchone()
        if not stats_row:
            total_points = 0
            valid_count = 0
            null_count = 0
            min_val = None
            max_val = None
            mean_val = None
            min_time = None
            max_time = None
        else:
            total_points = stats_row[0] or 0
            valid_count = stats_row[1] or 0
            null_count = stats_row[2] or 0
            min_val = float(stats_row[3]) if stats_row[3] is not None else None
            max_val = float(stats_row[4]) if stats_row[4] is not None else None
            mean_val = float(stats_row[5]) if stats_row[5] is not None else None
            min_time = float(stats_row[6]) if stats_row[6] is not None else None
            max_time = float(stats_row[7]) if stats_row[7] is not None else None

        # Calculate sampling rate
        if total_points > 1 and max_time is not None and min_time is not None and max_time > min_time:
            sampling_rate_hz = round((total_points - 1) / (max_time - min_time), 2)
        else:
            sampling_rate_hz = 30.0

        telemetry: list[dict[str, Any]] = []
        downsampled = False

        if total_points == 0:
            return {
                "investigation_id": slug,
                "run_id": actual_run_id,
                "metric": query_metric,
                "sampling_rate_hz": sampling_rate_hz,
                "total_points": 0,
                "downsampled": False,
                "channels": NUMERIC_SENSOR_METRICS,
                "telemetry": [],
                "statistics": {
                    "min": None,
                    "max": None,
                    "mean": None,
                    "null_count": 0,
                    "valid_count": 0,
                },
            }

        # 2. Query telemetry data: raw vs downsampled
        if downsample_points is not None and downsample_points > 0 and total_points > downsample_points:
            downsampled = True
            if decimation_method == "window" or decimation_method == "decimate":
                # Stride window decimation: select actual observation points
                step = max(1, total_points // downsample_points)
                decimate_sql = f"""
                    WITH raw_data AS (
                        SELECT 
                            time_seconds, 
                            {query_metric} AS val,
                            ROW_NUMBER() OVER (ORDER BY time_seconds) AS rn
                        FROM read_parquet(?)
                        WHERE {filter_sql}
                    )
                    SELECT time_seconds, val
                    FROM raw_data
                    WHERE (rn % {step} = 1) OR (rn = {total_points})
                    ORDER BY time_seconds
                """
                rows = self.conn.execute(decimate_sql, params).fetchall()
                for row in rows:
                    t = float(row[0])
                    val = float(row[1]) if row[1] is not None else None
                    telemetry.append({"time_seconds": t, "value": val, "value_si": val})
            else:
                # Bucketed NTILE downsampling
                ntile_params = list(params)
                ntile_params.append(downsample_points)
                ntile_sql = f"""
                    WITH raw_data AS (
                        SELECT 
                            time_seconds, 
                            {query_metric} AS val
                        FROM read_parquet(?)
                        WHERE {filter_sql}
                        ORDER BY time_seconds
                    ),
                    bucketed AS (
                        SELECT 
                            time_seconds, 
                            val,
                            NTILE(?) OVER (ORDER BY time_seconds) AS bucket
                        FROM raw_data
                    )
                    SELECT
                        bucket,
                        ROUND(AVG(time_seconds), 4) AS time_seconds,
                        CASE 
                            WHEN COUNT(val) = 0 THEN NULL 
                            ELSE AVG(val) 
                        END AS val
                    FROM bucketed
                    GROUP BY bucket
                    ORDER BY bucket
                """
                rows = self.conn.execute(ntile_sql, ntile_params).fetchall()
                for row in rows:
                    t = float(row[1])
                    val = float(row[2]) if row[2] is not None else None
                    telemetry.append({"time_seconds": t, "value": val, "value_si": val})
        else:
            # Query all raw telemetry points
            raw_sql = f"""
                SELECT time_seconds, {query_metric} AS val
                FROM read_parquet(?)
                WHERE {filter_sql}
                ORDER BY time_seconds
            """
            rows = self.conn.execute(raw_sql, params).fetchall()
            for row in rows:
                t = float(row[0])
                val = float(row[1]) if row[1] is not None else None
                telemetry.append({"time_seconds": t, "value": val, "value_si": val})

        return {
            "investigation_id": slug,
            "run_id": actual_run_id,
            "metric": query_metric,
            "sampling_rate_hz": sampling_rate_hz,
            "total_points": total_points,
            "downsampled": downsampled,
            "channels": NUMERIC_SENSOR_METRICS,
            "telemetry": telemetry,
            "statistics": {
                "min": min_val,
                "max": max_val,
                "mean": mean_val,
                "null_count": null_count,
                "valid_count": valid_count,
            },
        }
