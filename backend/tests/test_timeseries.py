"""
Unit and Integration Tests for High-Frequency Sensor Timeseries Storage and Query Engine.
Tests Parquet columnar storage, DuckDB vectorized queries, downsampling decimation,
strict non-zero NULL preservation, and FastAPI endpoint backward compatibility.
"""

from pathlib import Path

from backend.app.timeseries import (
    SENSOR_TIMESERIES_SCHEMA,
    DuckDBTimeseriesEngine,
    TimeseriesStorageManager,
    ensure_flight_telemetry_seeded,
    generate_flight_telemetry_datasets,
)
from backend.app.timeseries.generator import (
    generate_acme_run,
    generate_bass_run,
    generate_flex_run,
)
from fastapi.testclient import TestClient


def test_parquet_storage_manager_lifecycle(tmp_path: Path):
    """Verifies creating, writing, checking existence, reading, and checksumming Parquet files."""
    mgr = TimeseriesStorageManager(base_dir=tmp_path)
    sample_records = [
        {
            "time_seconds": 0.0,
            "investigation_slug": "test-slug",
            "run_identifier": "RUN-001",
            "droplet_diameter_squared_mm2": 4.0,
            "soot_volume_fraction": None,
        },
        {
            "time_seconds": 1.0,
            "investigation_slug": "test-slug",
            "run_identifier": "RUN-001",
            "droplet_diameter_squared_mm2": 0.0,  # genuine 0.0
            "soot_volume_fraction": None,
        },
    ]

    # Write Parquet file
    out_file = mgr.write_run_parquet(sample_records, "test-slug", "RUN-001")
    assert out_file.is_file()
    assert mgr.run_exists("test-slug", "RUN-001")
    assert not mgr.run_exists("test-slug", "NON-EXISTENT")

    # Verify SHA-256 checksum
    checksum = mgr.compute_file_checksum(out_file)
    assert len(checksum) == 64
    assert int(checksum, 16) > 0

    # Read back PyArrow table
    tbl = mgr.read_parquet_table("test-slug", "RUN-001")
    assert tbl.num_rows == 2
    assert tbl.schema.equals(SENSOR_TIMESERIES_SCHEMA)

    # Check non-zero NULL preservation in PyArrow bitmasks
    assert tbl["soot_volume_fraction"].null_count == 2
    assert tbl["droplet_diameter_squared_mm2"].null_count == 0
    assert tbl["droplet_diameter_squared_mm2"].to_pylist() == [4.0, 0.0]

    # List runs
    runs = mgr.list_runs("test-slug")
    assert len(runs) == 1
    assert runs[0]["run_identifier"] == "RUN-001"


def test_schema_conformance_and_data_types():
    """Verifies PyArrow schema conforms to required NASA microgravity physical channels."""
    field_names = SENSOR_TIMESERIES_SCHEMA.names
    assert "time_seconds" in field_names
    assert "investigation_slug" in field_names
    assert "run_identifier" in field_names
    assert "droplet_diameter_squared_mm2" in field_names
    assert "burning_rate_instantaneous_mm2_s" in field_names
    assert "radiant_flux_w" in field_names
    assert "chamber_pressure_kpa" in field_names
    assert "flame_spread_rate_mm_s" in field_names
    assert "soot_volume_fraction" in field_names
    assert "validation_status" in field_names

    # Check required nullability
    assert not SENSOR_TIMESERIES_SCHEMA.field("time_seconds").nullable
    assert not SENSOR_TIMESERIES_SCHEMA.field("investigation_slug").nullable
    assert not SENSOR_TIMESERIES_SCHEMA.field("run_identifier").nullable
    assert SENSOR_TIMESERIES_SCHEMA.field("droplet_diameter_squared_mm2").nullable
    assert SENSOR_TIMESERIES_SCHEMA.field("soot_volume_fraction").nullable


def test_flight_telemetry_generator_physics():
    """Verifies that generated datasets strictly adhere to microgravity combustion physics."""
    # 1. FLEX Heptane Droplet
    flex_pts = generate_flex_run("FLEX-001", d0_mm=2.0, burning_rate_k=0.65, sample_rate_hz=30.0, total_seconds=15.0)
    assert len(flex_pts) > 400
    # Strict unmeasured soot preservation in FLEX
    assert all(p["soot_volume_fraction"] is None for p in flex_pts)
    # Burning rates and burnout
    initial_d2 = flex_pts[0]["droplet_diameter_squared_mm2"]
    assert initial_d2 == 4.0
    burnout_pts = [p for p in flex_pts if p["droplet_diameter_squared_mm2"] == 0.0]
    assert len(burnout_pts) > 0, "Complete droplet burnout must produce genuine 0.0 measurements"
    # Never coerce None to 0.0 or 0.0 to None
    for p in flex_pts:
        assert p["soot_volume_fraction"] is None
        if p["time_seconds"] > 8.0:
            assert p["droplet_diameter_squared_mm2"] == 0.0
            assert p["droplet_diameter_squared_mm2"] is not None

    # 2. ACME Coflow Gas Flame
    acme_pts = generate_acme_run("ACME-CLD-001", fuel_flow_sccm=25.0, sample_rate_hz=10.0, total_seconds=30.0)
    assert len(acme_pts) == 301
    assert all(p["droplet_diameter_squared_mm2"] is None for p in acme_pts)
    assert all(p["soot_volume_fraction"] is not None and p["soot_volume_fraction"] > 0 for p in acme_pts)
    assert all(p["fuel_flow_rate_sccm"] is not None and p["fuel_flow_rate_sccm"] > 20.0 for p in acme_pts)

    # 3. BASS-II Solid Slab Flame Spread
    bass_pts = generate_bass_run("BASS-II-SLAB-001", spread_rate_mm_s=0.45, sample_rate_hz=5.0, total_seconds=60.0)
    assert len(bass_pts) == 301
    assert all(p["droplet_diameter_squared_mm2"] is None for p in bass_pts)
    assert all(p["flame_spread_rate_mm_s"] is not None and p["flame_spread_rate_mm_s"] > 0 for p in bass_pts)
    assert bass_pts[-1]["flame_position_mm"] > bass_pts[0]["flame_position_mm"]


def test_duckdb_engine_query_and_filtering(tmp_path: Path):
    """Verifies DuckDB query engine execution, time filters, and projection."""
    # Seed into temporary directory
    generate_flight_telemetry_datasets(output_dir=tmp_path)
    engine = DuckDBTimeseriesEngine(timeseries_dir=tmp_path)

    # Query without time filters
    res = engine.query_timeseries(
        "flex-2-heptane-droplet", "FLEX-001", "droplet_diameter_squared_mm2", downsample_points=0
    )
    assert res["total_points"] == 451
    assert res["downsampled"] is False
    assert len(res["telemetry"]) == 451
    assert res["statistics"]["max"] == 4.0
    assert res["statistics"]["min"] == 0.0

    # Query with time window filter [2.0, 5.0]
    res_filtered = engine.query_timeseries(
        "flex-2-heptane-droplet",
        "FLEX-001",
        "droplet_diameter_squared_mm2",
        start_time=2.0,
        end_time=5.0,
        downsample_points=0,
    )
    assert res_filtered["total_points"] > 0
    assert res_filtered["total_points"] < 451
    for pt in res_filtered["telemetry"]:
        assert pt["time_seconds"] >= 2.0
        assert pt["time_seconds"] <= 5.0


def test_duckdb_downsampling_decimation(tmp_path: Path):
    """Verifies bucketed downsampling via NTILE and window decimation."""
    generate_flight_telemetry_datasets(output_dir=tmp_path)
    engine = DuckDBTimeseriesEngine(timeseries_dir=tmp_path)

    # Bucketed NTILE downsampling
    res_ntile = engine.query_timeseries(
        "flex-2-heptane-droplet",
        "FLEX-001",
        "droplet_diameter_squared_mm2",
        downsample_points=50,
        decimation_method="ntile",
    )
    assert res_ntile["total_points"] == 451
    assert res_ntile["downsampled"] is True
    assert len(res_ntile["telemetry"]) == 50
    # Statistics should reflect full range
    assert res_ntile["statistics"]["min"] == 0.0
    assert res_ntile["statistics"]["max"] == 4.0

    # Window decimation
    res_dec = engine.query_timeseries(
        "flex-2-heptane-droplet",
        "FLEX-001",
        "droplet_diameter_squared_mm2",
        downsample_points=50,
        decimation_method="window",
    )
    assert res_dec["downsampled"] is True
    assert len(res_dec["telemetry"]) <= 60


def test_strict_non_zero_null_preservation(tmp_path: Path):
    """
    Critical Integrity Test:
    1. Missing sensor values must remain None/null and NEVER be coerced to 0.0.
    2. Genuine 0.0 measurements (complete burnout) must remain 0.0 and NEVER converted to null.
    """
    generate_flight_telemetry_datasets(output_dir=tmp_path)
    engine = DuckDBTimeseriesEngine(timeseries_dir=tmp_path)

    # 1. Test unmeasured sensor in FLEX (soot_volume_fraction)
    res_null = engine.query_timeseries(
        "flex-2-heptane-droplet",
        "FLEX-001",
        "soot_volume_fraction",
        downsample_points=100,
    )
    assert res_null["statistics"]["null_count"] == 451
    assert res_null["statistics"]["valid_count"] == 0
    assert res_null["statistics"]["min"] is None
    assert res_null["statistics"]["max"] is None
    for pt in res_null["telemetry"]:
        assert pt["value"] is None
        assert pt["value_si"] is None
        # Explicit check: None is strictly not 0.0
        assert pt["value"] != 0.0

    # 2. Test genuine 0.0 sensor readings in FLEX burnout
    res_zero = engine.query_timeseries(
        "flex-2-heptane-droplet",
        "FLEX-001",
        "droplet_diameter_squared_mm2",
        start_time=10.0,  # Fully burned out phase
        downsample_points=0,
    )
    assert res_zero["total_points"] > 0
    assert res_zero["statistics"]["null_count"] == 0
    assert res_zero["statistics"]["min"] == 0.0
    assert res_zero["statistics"]["max"] == 0.0
    for pt in res_zero["telemetry"]:
        assert pt["value"] == 0.0
        assert pt["value_si"] == 0.0
        assert pt["value"] is not None


def test_timeseries_api_endpoint_backward_compatibility(client: TestClient):
    """Confirms 100% backward compatibility with legacy test_investigation_timeseries_endpoint."""
    ensure_flight_telemetry_seeded()
    res = client.get("/api/v1/investigations/flex-2-heptane-droplet/timeseries")
    assert res.status_code == 200
    data = res.json()
    assert data["investigation_id"] == "flex-2-heptane-droplet"
    assert "measurements" in data
    assert isinstance(data["measurements"], dict)


def test_timeseries_api_endpoint_rich_telemetry(client: TestClient):
    """Verifies upgraded endpoint returns rich telemetry payload with statistics and channels."""
    ensure_flight_telemetry_seeded()
    res = client.get(
        "/api/v1/investigations/flex-2-heptane-droplet/timeseries?run_id=FLEX-001&metric=droplet_diameter_squared_mm2&downsample_points=100"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["investigation_id"] == "flex-2-heptane-droplet"
    assert data["run_id"] == "FLEX-001"
    assert data["metric"] == "droplet_diameter_squared_mm2"
    assert data["downsampled"] is True
    assert data["total_points"] == 451
    assert len(data["telemetry"]) == 100
    assert data["sampling_rate_hz"] > 0
    assert "statistics" in data
    assert data["statistics"]["min"] == 0.0
    assert data["statistics"]["max"] == 4.0
    assert data["statistics"]["valid_count"] == 451
    assert data["statistics"]["null_count"] == 0
    assert "channels" in data
    assert "droplet_diameter_squared_mm2" in data["channels"]


def test_timeseries_api_endpoint_null_preservation_via_http(client: TestClient):
    """Verifies that HTTP JSON response preserves null for unmeasured channels."""
    ensure_flight_telemetry_seeded()
    res = client.get(
        "/api/v1/investigations/flex-2-heptane-droplet/timeseries?run_id=FLEX-001&metric=soot_volume_fraction"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["statistics"]["null_count"] == 451
    assert data["statistics"]["valid_count"] == 0
    assert data["statistics"]["min"] is None
    # All telemetry values in JSON must serialize as null
    for pt in data["telemetry"]:
        assert pt["value"] is None
        assert pt["value_si"] is None


def test_timeseries_api_endpoint_acme_and_bass(client: TestClient):
    """Verifies endpoint handles ACME gas burner and BASS-II solid slab runs."""
    ensure_flight_telemetry_seeded()

    # ACME co-flow flame
    res_acme = client.get(
        "/api/v1/investigations/acme-cld-flame/timeseries?run_id=ACME-CLD-001&metric=soot_volume_fraction"
    )
    assert res_acme.status_code == 200
    data_acme = res_acme.json()
    assert data_acme["investigation_id"] == "acme-cld-flame"
    assert data_acme["statistics"]["valid_count"] > 0
    assert data_acme["statistics"]["min"] > 0

    # BASS-II solid slab
    res_bass = client.get(
        "/api/v1/investigations/bass-ii-solid-slab/timeseries?run_id=BASS-II-SLAB-001&metric=flame_spread_rate_mm_s"
    )
    assert res_bass.status_code == 200
    data_bass = res_bass.json()
    assert data_bass["investigation_id"] == "bass-ii-solid-slab"
    assert data_bass["statistics"]["valid_count"] > 0


def test_timeseries_api_endpoint_error_handling(client: TestClient):
    """Verifies 404 for nonexistent investigation and 422 for invalid/injected metric."""
    # Nonexistent investigation
    res_404 = client.get("/api/v1/investigations/non-existent-slug/timeseries")
    assert res_404.status_code == 404

    # Invalid metric name
    res_422 = client.get("/api/v1/investigations/flex-2-heptane-droplet/timeseries?metric=DROP_TABLE_sensor;--")
    assert res_422.status_code == 422
