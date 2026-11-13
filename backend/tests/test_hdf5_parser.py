"""Unit tests for NASA CIR HDF5 Multi-Channel Flight Telemetry Parser.

Verifies:
- Hierarchical dataset parsing (metadata + sensor channels).
- Strict non-zero NULL preservation for missing/flagged measurements.
- SHA-256 cryptographic provenance integrity.
- Channel statistical summaries.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from backend.app.ingestion.parsers.hdf5_parser import (
    HDF5FlightParser,
    HDF5FlightRunSummary,
    RadiometerChannelData,
)


@pytest.fixture
def temp_h5_file(tmp_path: Path) -> Path:
    fixture_path = tmp_path / "test_cir_flight_run.h5"
    return HDF5FlightParser.create_synthetic_test_fixture(
        dest_path=fixture_path,
        investigation_slug="flex-2-heptane-droplet",
        num_points=100,
        inject_missing_sensor=True,
    )


def test_hdf5_sha256_provenance(temp_h5_file: Path):
    digest = HDF5FlightParser.calculate_sha256(temp_h5_file)
    assert isinstance(digest, str)
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_hdf5_parser_metadata_and_channels(temp_h5_file: Path):
    summary = HDF5FlightParser.parse_flight_file(temp_h5_file)

    assert isinstance(summary, HDF5FlightRunSummary)
    assert summary.investigation_slug == "flex-2-heptane-droplet"
    assert summary.facility == "Combustion Integrated Rack (CIR)"
    assert summary.run_identifier == "CIR-FLEX2-RUN-042"
    assert summary.fuel == "n-heptane"
    assert summary.ambient_o2_pct == 21.0
    assert summary.ambient_pressure_kpa == 101.325
    assert summary.gravity_regime == "microgravity (~10^-6 g)"
    assert summary.channel_count == 2
    assert "broadband_radiometer" in summary.channels
    assert "chamber_pressure" in summary.channels


def test_hdf5_parser_strict_null_preservation(temp_h5_file: Path):
    summary = HDF5FlightParser.parse_flight_file(temp_h5_file)
    rad_channel = summary.channels["broadband_radiometer"]

    assert rad_channel.total_samples == 100
    assert len(rad_channel.values) == 100

    # Indices 15-19 were injected with -9999.0 missing sentinel
    for idx in range(15, 20):
        assert rad_channel.values[idx] is None, f"Sample at index {idx} should be None, not 0.0 or sentinel"

    # Index 50 was injected with explicit NaN
    assert rad_channel.values[50] is None

    # Valid values should be floats
    assert isinstance(rad_channel.values[0], float)
    assert rad_channel.values[0] > 0.0


def test_hdf5_parser_channel_statistics(temp_h5_file: Path):
    summary = HDF5FlightParser.parse_flight_file(temp_h5_file)
    p_channel = summary.channels["chamber_pressure"]

    assert p_channel.unit == "kPa"
    assert p_channel.sample_rate_hz == 10.0
    assert p_channel.min_val is not None
    assert p_channel.max_val is not None
    assert p_channel.mean_val is not None
    assert 101.0 <= p_channel.mean_val <= 102.0


def test_hdf5_parser_nonexistent_file_raises(tmp_path: Path):
    invalid_path = tmp_path / "does_not_exist.h5"
    with pytest.raises(FileNotFoundError):
        HDF5FlightParser.parse_flight_file(invalid_path)
