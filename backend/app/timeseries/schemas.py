"""
Schemas and DTOs for High-Frequency Timeseries Telemetry.
Includes PyArrow columnar schema definitions and Pydantic response models.
"""

from typing import Any

import pyarrow as pa
from pydantic import BaseModel, ConfigDict, Field

# PyArrow Columnar Telemetry Schema
# Conforms to NASA microgravity physical channels and strict non-zero NULL semantics
SENSOR_TIMESERIES_SCHEMA = pa.schema(
    [
        pa.field("time_seconds", pa.float64(), nullable=False),
        pa.field("investigation_slug", pa.string(), nullable=False),
        pa.field("run_identifier", pa.string(), nullable=False),
        # Droplet combustion channels (FLEX / FLEX-2)
        pa.field("droplet_diameter_mm", pa.float64(), nullable=True),
        pa.field("droplet_diameter_squared_mm2", pa.float64(), nullable=True),
        pa.field("burning_rate_instantaneous_mm2_s", pa.float64(), nullable=True),
        # Radiometry & Environmental channels
        pa.field("radiant_flux_w", pa.float64(), nullable=True),
        pa.field("chamber_pressure_kpa", pa.float64(), nullable=True),
        pa.field("ambient_temperature_k", pa.float64(), nullable=True),
        # Solid spread & diffusion channels (BASS-II & ACME)
        pa.field("flame_spread_rate_mm_s", pa.float64(), nullable=True),
        pa.field("flame_position_mm", pa.float64(), nullable=True),
        pa.field("fuel_flow_rate_sccm", pa.float64(), nullable=True),
        pa.field("soot_volume_fraction", pa.float64(), nullable=True),
        # Provenance & Validation Status
        pa.field("validation_status", pa.string(), nullable=True),
        pa.field("is_extinguished", pa.bool_(), nullable=True),
    ]
)

# Recognized sensor metric columns available for query projection
NUMERIC_SENSOR_METRICS: list[str] = [
    "droplet_diameter_mm",
    "droplet_diameter_squared_mm2",
    "burning_rate_instantaneous_mm2_s",
    "radiant_flux_w",
    "chamber_pressure_kpa",
    "ambient_temperature_k",
    "flame_spread_rate_mm_s",
    "flame_position_mm",
    "fuel_flow_rate_sccm",
    "soot_volume_fraction",
]


class TelemetryPoint(BaseModel):
    """Single timeseries observation point with non-zero NULL preservation."""

    time_seconds: float
    value: float | None = None
    value_si: float | None = None

    model_config = ConfigDict(from_attributes=True)


class TimeseriesStats(BaseModel):
    """Summary statistics calculated over valid non-null telemetry points."""

    min: float | None = None
    max: float | None = None
    mean: float | None = None
    null_count: int = 0
    valid_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TimeseriesResponse(BaseModel):
    """
    Standard timeseries API response payload.
    Preserves backward compatibility with legacy 'investigation_id', 'run_id', 'metric',
    and 'measurements' keys while providing high-frequency telemetry and window statistics.
    """

    investigation_id: str
    run_id: str | None = None
    metric: str | None = None
    measurements: dict[str, Any] = Field(default_factory=dict)
    sampling_rate_hz: float | None = 30.0
    total_points: int = 0
    downsampled: bool = False
    channels: list[str] = Field(default_factory=list)
    telemetry: list[TelemetryPoint] = Field(default_factory=list)
    statistics: TimeseriesStats | None = None

    model_config = ConfigDict(from_attributes=True)
