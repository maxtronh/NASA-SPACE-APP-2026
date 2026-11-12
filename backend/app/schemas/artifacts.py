"""Discriminated union Pydantic v2 schemas for the 6 Generative UI Scientific Artifact types.

Artifact Types:
  - chart: Interactive 2D Recharts/Plotly chart
  - flame3d: Three.js / WebGL spherical flame simulation
  - timeseries: Multichannel sensor telemetry viewer
  - table: Formatted scientific data table
  - citation: Verified citation card with BibTeX modal
  - equation: LaTeX math equation viewer (KaTeX)
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------


class ArtifactBase(BaseModel):
    """Common fields shared by every artifact."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None


# ---------------------------------------------------------------------------
# 1. Chart artifact
# ---------------------------------------------------------------------------


class ChartDataSeries(BaseModel):
    """A single data series within a chart artifact."""

    name: str
    data_key: str
    color: str | None = None
    unit: str | None = None


class ChartArtifact(ArtifactBase):
    """Interactive 2D chart (Recharts / Plotly)."""

    artifact_type: Literal["chart"] = "chart"
    chart_type: Literal["line", "bar", "scatter", "area"] = "line"
    x_label: str = "x"
    y_label: str = "y"
    x_unit: str | None = None
    y_unit: str | None = None
    series: list[ChartDataSeries] = Field(default_factory=list)
    data_points: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 2. Flame3D artifact
# ---------------------------------------------------------------------------


class Flame3DArtifact(ArtifactBase):
    """Three.js / WebGL spherical flame simulation placeholder."""

    artifact_type: Literal["flame3d"] = "flame3d"
    droplet_diameter_mm: float | None = None
    burning_rate_mm2_s: float | None = None
    ambient_o2_pct: float | None = None
    flame_mode: Literal["hot", "cool", "dual"] = "hot"


# ---------------------------------------------------------------------------
# 3. Timeseries artifact
# ---------------------------------------------------------------------------


class TimeseriesChannel(BaseModel):
    """A single telemetry channel in a timeseries artifact."""

    channel_name: str
    unit: str | None = None
    color: str | None = None
    data_key: str | None = None


class TimeseriesArtifact(ArtifactBase):
    """Multichannel sensor telemetry viewer."""

    artifact_type: Literal["timeseries"] = "timeseries"
    investigation_id: str | None = None
    sampling_rate_hz: float | None = None
    channels: list[TimeseriesChannel] = Field(default_factory=list)
    time_range_s: tuple[float, float] | None = None
    data_points: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 4. Table artifact
# ---------------------------------------------------------------------------


class TableColumn(BaseModel):
    """Column definition for a scientific data table."""

    key: str
    label: str
    unit: str | None = None
    format: str | None = None  # e.g. ".3f"


class TableArtifact(ArtifactBase):
    """Formatted scientific data table."""

    artifact_type: Literal["table"] = "table"
    columns: list[TableColumn] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    source_investigation: str | None = None


# ---------------------------------------------------------------------------
# 5. Citation artifact
# ---------------------------------------------------------------------------


class CitationArtifact(ArtifactBase):
    """Verified citation card with BibTeX modal."""

    artifact_type: Literal["citation"] = "citation"
    investigation_id: str
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    year: int | None = None
    doi: str | None = None
    nasa_source_url: str | None = None
    bibtex: str | None = None


# ---------------------------------------------------------------------------
# 6. Equation artifact
# ---------------------------------------------------------------------------


class EquationArtifact(ArtifactBase):
    """LaTeX math equation viewer (KaTeX)."""

    artifact_type: Literal["equation"] = "equation"
    latex: str = Field(..., min_length=1)
    display_mode: bool = True
    context: str | None = None


# ---------------------------------------------------------------------------
# Discriminated union
# ---------------------------------------------------------------------------

ScientificArtifact = Annotated[
    Union[
        ChartArtifact,
        Flame3DArtifact,
        TimeseriesArtifact,
        TableArtifact,
        CitationArtifact,
        EquationArtifact,
    ],
    Field(discriminator="artifact_type"),
]
