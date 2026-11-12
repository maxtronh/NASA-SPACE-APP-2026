"""Unit tests for Generative UI Scientific Artifact schemas, discriminated union, and pipeline integration.

Upgrade 17 Verification:
- 6 Discriminated artifact types: chart, flame3d, timeseries, table, citation, equation.
- Zero data fabrication and strict non-zero NULL preservation (None stays None, never coerced to 0.0).
- Deserialization and validation via TypeAdapter / BaseModel.
- Integration with SIQueryResponse and ScientificIntelligencePipeline.
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from backend.app.ml.pipeline import ScientificIntelligencePipeline, _generate_artifacts
from backend.app.schemas.artifacts import (
    ChartArtifact,
    ChartDataSeries,
    CitationArtifact,
    EquationArtifact,
    Flame3DArtifact,
    ScientificArtifact,
    TableArtifact,
    TableColumn,
    TimeseriesArtifact,
    TimeseriesChannel,
)
from backend.app.schemas.si import SIQueryResponse


# ---------------------------------------------------------------------------
# Schema & Discriminated Union Tests
# ---------------------------------------------------------------------------


def test_chart_artifact_validation():
    data = {
        "artifact_type": "chart",
        "title": "FLEX d²-Law Burning Rate",
        "description": "Squared droplet diameter vs time",
        "chart_type": "line",
        "x_label": "Time",
        "y_label": "d²",
        "x_unit": "s",
        "y_unit": "mm²",
        "series": [{"name": "d²(t)", "data_key": "d2", "color": "#06b6d4", "unit": "mm²"}],
        "data_points": [{"t": 0.0, "d2": 4.0}, {"t": 1.0, "d2": 3.42}],
    }
    adapter = TypeAdapter(ScientificArtifact)
    art = adapter.validate_python(data)
    assert isinstance(art, ChartArtifact)
    assert art.artifact_type == "chart"
    assert art.chart_type == "line"
    assert len(art.series) == 1
    assert art.series[0].data_key == "d2"


def test_flame3d_artifact_null_preservation():
    """Verify strict NULL preservation: missing measurements are None, NOT coerced to 0.0."""
    data = {
        "artifact_type": "flame3d",
        "title": "Spherical Flame Envelope",
        "droplet_diameter_mm": None,
        "burning_rate_mm2_s": None,
        "ambient_o2_pct": None,
        "flame_mode": "cool",
    }
    art = Flame3DArtifact(**data)
    assert art.droplet_diameter_mm is None
    assert art.burning_rate_mm2_s is None
    assert art.ambient_o2_pct is None
    assert art.flame_mode == "cool"


def test_timeseries_artifact_validation():
    data = {
        "artifact_type": "timeseries",
        "title": "Chamber Thermocouple Array",
        "investigation_id": "flex-droplet-burning",
        "sampling_rate_hz": 100.0,
        "channels": [
            {"channel_name": "TC-1", "unit": "K", "color": "#ef4444", "data_key": "tc1"},
            {"channel_name": "TC-2", "unit": "K", "color": "#f59e0b", "data_key": "tc2"},
        ],
        "time_range_s": (0.0, 10.5),
        "data_points": [{"t": 0.0, "tc1": 298.15, "tc2": 298.15}],
    }
    art = TimeseriesArtifact(**data)
    assert art.artifact_type == "timeseries"
    assert len(art.channels) == 2
    assert art.time_range_s == (0.0, 10.5)


def test_table_artifact_validation():
    data = {
        "artifact_type": "table",
        "title": "Benchmark Extinction Diameters",
        "columns": [
            {"key": "fuel", "label": "Fuel Type"},
            {"key": "d0", "label": "Initial Diameter", "unit": "mm", "format": ".2f"},
            {"key": "d_ext", "label": "Extinction Diameter", "unit": "mm", "format": ".2f"},
        ],
        "rows": [
            {"fuel": "n-heptane", "d0": 3.0, "d_ext": 0.84},
            {"fuel": "methanol", "d0": 2.5, "d_ext": None},
        ],
        "source_investigation": "flex-2",
    }
    art = TableArtifact(**data)
    assert art.artifact_type == "table"
    assert len(art.columns) == 3
    assert art.rows[1]["d_ext"] is None  # Strict NULL preserved


def test_citation_artifact_validation():
    data = {
        "artifact_type": "citation",
        "title": "FLEX Microgravity Droplet Combustion Observations",
        "investigation_id": "flex-droplet-burning",
        "authors": ["Forman A. Williams", "Vedha Nayagam"],
        "journal": "Combustion and Flame",
        "year": 2015,
        "doi": "10.1016/j.combustflame.2015.01.001",
        "nasa_source_url": "https://ntrs.nasa.gov/citations/20150023456",
        "bibtex": "@article{williams2015flex, title={FLEX Droplets}}",
    }
    art = CitationArtifact(**data)
    assert art.artifact_type == "citation"
    assert art.year == 2015
    assert art.doi == "10.1016/j.combustflame.2015.01.001"


def test_equation_artifact_validation():
    data = {
        "artifact_type": "equation",
        "title": "d²-Law Governing Equation",
        "latex": r"d^2(t) = d_0^2 - K \cdot t",
        "display_mode": True,
        "context": "Classical d²-law burning rate decay.",
    }
    art = EquationArtifact(**data)
    assert art.artifact_type == "equation"
    assert art.display_mode is True
    assert "d^2(t)" in art.latex


def test_discriminated_union_invalid_type_raises():
    adapter = TypeAdapter(ScientificArtifact)
    with pytest.raises(ValidationError):
        adapter.validate_python({
            "artifact_type": "unsupported_unknown_type",
            "title": "Invalid Artifact",
        })


def test_discriminated_union_all_types():
    adapter = TypeAdapter(ScientificArtifact)
    types_payloads = [
        {"artifact_type": "chart", "title": "Chart"},
        {"artifact_type": "flame3d", "title": "Flame3D"},
        {"artifact_type": "timeseries", "title": "Timeseries"},
        {"artifact_type": "table", "title": "Table"},
        {"artifact_type": "citation", "title": "Citation", "investigation_id": "test"},
        {"artifact_type": "equation", "title": "Equation", "latex": "E=mc^2"},
    ]
    for p in types_payloads:
        art = adapter.validate_python(p)
        assert art.artifact_type == p["artifact_type"]
        assert art.title == p["title"]


# ---------------------------------------------------------------------------
# SIQueryResponse Integration
# ---------------------------------------------------------------------------


def test_si_query_response_with_artifacts():
    response_payload = {
        "query": "How do droplets burn in microgravity?",
        "answer": "Droplets burn with spherical symmetry according to the d²-law.",
        "confidence_score": 0.92,
        "abstention_flag": False,
        "citations": [
            {
                "investigation_id": "flex-droplet-burning",
                "title": "Flame Extinguishment Experiment (FLEX)",
                "nasa_source_url": "https://ntrs.nasa.gov/citations/20150023456",
                "relevance_score": 0.95,
            }
        ],
        "explainability": {
            "matched_entities": ["droplet", "combustion"],
            "retrieval_method": "hybrid_rrf_bm25_vector",
            "abstention_reason": None,
        },
        "artifacts": [
            {
                "artifact_type": "equation",
                "title": "d²-Law",
                "latex": "d^2(t) = d_0^2 - K t",
                "display_mode": True,
            },
            {
                "artifact_type": "flame3d",
                "title": "Spherical Flame Envelope",
                "droplet_diameter_mm": None,
            },
        ],
    }
    parsed = SIQueryResponse(**response_payload)
    assert len(parsed.artifacts) == 2
    assert isinstance(parsed.artifacts[0], EquationArtifact)
    assert isinstance(parsed.artifacts[1], Flame3DArtifact)
    assert parsed.artifacts[1].droplet_diameter_mm is None


# ---------------------------------------------------------------------------
# Pipeline Generation Tests
# ---------------------------------------------------------------------------


def test_pipeline_generate_artifacts_droplet_combustion():
    artifacts = _generate_artifacts(
        query="What is the burning rate of droplet in FLEX?",
        answer="FLEX observes spherical burning of isolated droplets.",
        matched_entities=["droplet", "flex"],
        citations=[{"investigation_id": "flex-droplet-burning", "title": "FLEX"}],
        retrieved_docs=[
            {
                "slug": "flex-droplet-burning",
                "title": "FLEX Droplet Burning",
                "combustion_regime": "droplet_combustion",
                "relevance_score": 0.9,
            }
        ],
    )

    types = [a["artifact_type"] for a in artifacts]
    assert "equation" in types
    assert "citation" in types
    assert "chart" in types
    assert "flame3d" in types
    assert "table" in types
    assert "timeseries" in types

    # Check NULL preservation
    flame_art = next(a for a in artifacts if a["artifact_type"] == "flame3d")
    assert flame_art["droplet_diameter_mm"] is None
    assert flame_art["burning_rate_mm2_s"] is None


def test_pipeline_process_query_droplet_has_artifacts():
    pipeline = ScientificIntelligencePipeline()
    res = pipeline.process_query("What is droplet combustion in microgravity FLEX?")
    assert not res["abstention_flag"]
    assert len(res["artifacts"]) >= 3
    artifact_types = [a["artifact_type"] for a in res["artifacts"]]
    assert "equation" in artifact_types
    assert "citation" in artifact_types


def test_pipeline_process_query_abstention_artifacts_empty():
    pipeline = ScientificIntelligencePipeline()
    res = pipeline.process_query("quantum entangled superstrings in multiverse")
    assert res["abstention_flag"]
    assert res["artifacts"] == []
