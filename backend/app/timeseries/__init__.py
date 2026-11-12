"""
Timeseries package for Apache Parquet storage and DuckDB in-process analytics.
"""

from backend.app.timeseries.engine import DuckDBTimeseriesEngine
from backend.app.timeseries.generator import (
    ensure_flight_telemetry_seeded,
    generate_flight_telemetry_datasets,
)
from backend.app.timeseries.schemas import (
    NUMERIC_SENSOR_METRICS,
    SENSOR_TIMESERIES_SCHEMA,
    TelemetryPoint,
    TimeseriesResponse,
    TimeseriesStats,
)
from backend.app.timeseries.storage import TimeseriesStorageManager

__all__ = [
    "NUMERIC_SENSOR_METRICS",
    "SENSOR_TIMESERIES_SCHEMA",
    "DuckDBTimeseriesEngine",
    "TelemetryPoint",
    "TimeseriesResponse",
    "TimeseriesStats",
    "TimeseriesStorageManager",
    "ensure_flight_telemetry_seeded",
    "generate_flight_telemetry_datasets",
]
