"""
Automated Test Suite for NASA Data Ingestion Pipeline & Provenance Engine.
Tests:
  1. Live and cached NTRS API fetching.
  2. SHA-256 cryptographic provenance calculation and tamper detection.
  3. Deterministic SI unit normalization across all physical dimensions.
  4. Strict Non-Zero NULL preservation (Acceptance Rule #4: missing is NULL, never 0.0).
  5. Authentic flight table parsers (FLEX Table IX, BASS-II Table 5.1, ACME CLD).
  6. Schema conformance with docs/PROJECT_ARCHITECTURE.md and PROJECT.md.
"""

import json
import math
import os
import sys
import pytest

# Ensure both workspace root and backend root are in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

try:
    from backend.app.ingestion.fetcher import NASADataFetcher
    from backend.app.ingestion.normalizer import (
        convert_burning_rate_to_m2_s,
        convert_flow_rate_to_m3_s,
        convert_length_to_m,
        convert_pressure_to_pa,
        convert_temperature_to_kelvin,
        convert_velocity_to_m_s,
        is_null_or_unobserved,
        normalize_to_si,
    )
    from backend.app.ingestion.parsers import ACMEParser, BASSParser, FLEXParser
    from backend.app.ingestion.preserver import (
        calculate_sha256,
        save_raw_payload,
        verify_provenance_integrity,
    )
except ImportError:
    from app.ingestion.fetcher import NASADataFetcher
    from app.ingestion.normalizer import (
        convert_burning_rate_to_m2_s,
        convert_flow_rate_to_m3_s,
        convert_length_to_m,
        convert_pressure_to_pa,
        convert_temperature_to_kelvin,
        convert_velocity_to_m_s,
        is_null_or_unobserved,
        normalize_to_si,
    )
    from app.ingestion.parsers import ACMEParser, BASSParser, FLEXParser
    from app.ingestion.preserver import (
        calculate_sha256,
        save_raw_payload,
        verify_provenance_integrity,
    )


# ==============================================================================
# 1. NTRS FETCHER & CACHE TESTS
# ==============================================================================

def test_fetcher_cached_citation(tmp_path):
    """Verifies that fetcher correctly caches and reads citation payloads."""
    fetcher = NASADataFetcher(raw_dir=tmp_path)
    sample_data = {"id": 12345, "title": "Test Microgravity Combustion"}
    save_raw_payload("12345_citation.json", json.dumps(sample_data), raw_dir=tmp_path)

    result = fetcher.fetch_citation("12345", force_refresh=False)
    assert result["id"] == 12345
    assert result["title"] == "Test Microgravity Combustion"


def test_fetcher_save_raw_payload_creates_meta(tmp_path):
    """Verifies that saving a raw payload creates a companion .meta.json file."""
    content = b"Authentic NASA Flight Data Stream"
    saved_path = save_raw_payload(
        "flight_telemetry.bin",
        content,
        metadata={"source_url": "https://ntrs.nasa.gov/citations/test"},
        raw_dir=tmp_path
    )
    assert saved_path.is_file()

    meta_path = tmp_path / "flight_telemetry.bin.meta.json"
    assert meta_path.is_file()

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["filename"] == "flight_telemetry.bin"
    assert meta["byte_size"] == len(content)
    assert "sha256_checksum" in meta
    assert len(meta["sha256_checksum"]) == 64


# ==============================================================================
# 2. SHA-256 PROVENANCE & TAMPER DETECTION TESTS
# ==============================================================================

def test_sha256_deterministic_calculation():
    """Verifies cryptographic hash consistency across strings, bytes, and JSON dicts."""
    text = "FLEX-2 Droplet Combustion ISS CIR"
    hash1 = calculate_sha256(text)
    hash2 = calculate_sha256(text.encode("utf-8"))
    assert hash1 == hash2
    assert len(hash1) == 64

    dict_a = {"pressure": 101.3, "fuel": "Heptane"}
    dict_b = {"fuel": "Heptane", "pressure": 101.3}
    assert calculate_sha256(dict_a) == calculate_sha256(dict_b)


def test_tamper_detection(tmp_path):
    """Verifies that bitwise modification of raw payload is immediately detected."""
    file_path = tmp_path / "tamper_test.txt"
    original_data = b"Authentic NASA Data: Table IX test 001"
    file_path.write_bytes(original_data)

    checksum = calculate_sha256(original_data)
    assert verify_provenance_integrity(file_path, checksum) is True

    # Tamper with one byte
    file_path.write_bytes(b"Tampered NASA Data: Table IX test 001")
    assert verify_provenance_integrity(file_path, checksum) is False


# ==============================================================================
# 3. DETERMINISTIC SI UNIT NORMALIZATION TESTS
# ==============================================================================

def test_si_pressure_conversions():
    """Tests pressure conversion across all aerospace units to Pascals."""
    p_psi = convert_pressure_to_pa(14.7, "psi")
    assert math.isclose(p_psi, 14.7 * 6894.757293, abs_tol=1e-3)

    p_atm = convert_pressure_to_pa(1.0, "atm")
    assert math.isclose(p_atm, 101325.0, abs_tol=1e-3)

    p_mmhg = convert_pressure_to_pa(760.0, "mmHg")
    assert math.isclose(p_mmhg, 101325.0, abs_tol=1e-2)

    p_kpa = convert_pressure_to_pa(101.3, "kPa")
    assert math.isclose(p_kpa, 101300.0, abs_tol=1e-3)

    p_bar = convert_pressure_to_pa(1.0, "bar")
    assert math.isclose(p_bar, 100000.0, abs_tol=1e-3)


def test_si_velocity_and_burning_rate():
    """Tests velocity and droplet d^2 burning rate conversions to SI."""
    v_ms = convert_velocity_to_m_s(20.0, "cm/s")
    assert math.isclose(v_ms, 0.20, abs_tol=1e-5)

    v_mms = convert_velocity_to_m_s(0.85, "mm/s")
    assert math.isclose(v_mms, 0.00085, abs_tol=1e-7)

    k_m2s = convert_burning_rate_to_m2_s(0.78, "mm^2/s")
    assert math.isclose(k_m2s, 7.8e-7, abs_tol=1e-10)


def test_si_length_temperature_and_flow():
    """Tests length, temperature, and volumetric flow rate conversions to SI."""
    d_m = convert_length_to_m(2.1, "mm")
    assert math.isclose(d_m, 0.0021, abs_tol=1e-6)

    d_in = convert_length_to_m(0.25, "in")
    assert math.isclose(d_in, 0.00635, abs_tol=1e-6)

    t_k_f = convert_temperature_to_kelvin(77.0, "degF")
    assert math.isclose(t_k_f, 298.15, abs_tol=1e-2)

    t_k_c = convert_temperature_to_kelvin(25.0, "degC")
    assert math.isclose(t_k_c, 298.15, abs_tol=1e-2)

    q_si = convert_flow_rate_to_m3_s(25.0, "sccm")
    assert math.isclose(q_si, 4.166667e-7, rel_tol=1e-4)


# ==============================================================================
# 4. STRICT NON-ZERO NULL PRESERVATION TESTS (Rule #4)
# ==============================================================================

@pytest.mark.parametrize("missing_token", [
    "–",   # Unicode en-dash
    "—",   # Unicode em-dash
    "-",   # ASCII hyphen
    "N/A",
    "NA",
    "null",
    "None",
    "ND",
    "unmeasured",
    "unobserved",
    "Not tracked",
    "",
    None,
])
def test_non_zero_null_rule(missing_token):
    """
    MANDATORY CRITICAL TEST:
    Verifies that missing/unobserved scientific data is preserved as Python None.
    Under NO circumstances may missing data be coerced or substituted with 0.0 or 0!
    """
    assert is_null_or_unobserved(missing_token) is True

    val_si, _unit_si, method, status = normalize_to_si("visible_extinction_diameter", missing_token, "mm")
    assert val_si is None, f"VIOLATION: token '{missing_token}' was normalized to {val_si} instead of None"
    assert status == "MISSING_DATA"
    assert method == "null_preservation"


def test_zero_is_not_treated_as_null():
    """Verifies that genuine physical zero (0.0 m/s) is preserved and NOT treated as NULL."""
    assert is_null_or_unobserved(0.0) is False
    assert is_null_or_unobserved(0) is False

    val_si, _unit_si, _method, status = normalize_to_si("velocity", 0.0, "m/s")
    assert val_si == 0.0
    assert status == "VALID"


# ==============================================================================
# 5. FLIGHT TABLE PARSER TESTS
# ==============================================================================

def test_flex_parser_table_ix():
    """Tests parsing Table IX of FLEX report 20150023456."""
    parser = FLEXParser()
    sample_text = """
    TABLE IX.—RESULTS BY TEST NUMBER AND FLEX IDENTIFIER
    Fuel Ambient Initial ambient Droplet Visible Burning
    pressure, composition, initial flame rate, Burn Test end
    mmHg mole fraction diameter, extinction mm2/s time,
    Greenwich O2 N2 CO2 He mm diameter, s
    mean time mm
    Test Date

    FLEX–001 20CAL08 3/5/09 17:22:03 Methanol 757.7 0.21 0.79 0 0 1.69 0.89 0.52 4.3 Disruption

    FLEX–004 30CAL02 3/31/09 17:16:18 Methanol 760 .21 .79 0 0 2.06 – .6 7.64 Extinction

    FLEX–007 20CAL13 4/10/09 13:26:11 Heptane 761.3 .21 .79 0 0 1.87 – .67 5.3 Disruption
    """
    payload = parser.parse(sample_text, {"title": "FLEX Droplet Burning"})
    assert payload.investigation.slug == "flex-droplet-burning"
    assert payload.investigation.combustion_regime == "droplet_combustion"
    assert len(payload.test_runs) >= 3

    run_001 = payload.test_runs[0]
    assert run_001.run_identifier == "FLEX-001"
    assert run_001.droplet_initial_diameter_mm == 1.69
    assert run_001.burning_rate_constant_k_mm2_s == 0.52
    assert run_001.extinction_type == "disruption"

    run_004 = payload.test_runs[1]
    assert run_004.run_identifier == "FLEX-004"
    assert run_004.si_normalized_parameters["extinction_diameter_m"] is None

    run_007 = payload.test_runs[2]
    assert run_007.run_identifier == "FLEX-007"
    assert run_007.raw_parameters["fuel"] == "n-Heptane"


def test_bass_parser_table_51():
    """Tests parsing Table 5.1 of BASS-II report 20210011385."""
    parser = BASSParser()
    sample_text = """
    TABLE 5.1.—TWENTY BURNING AND SUPPRESSION OF SOLIDS—II (BASS–II) TESTS 
    Test no. Thickness, mm Width, cm One or two sides burning Velocity, cm/s Spread rate, mm/s Burn time, min Initial O2, vol% Final O2, vol% 

    M1 1 2.2 1 9 0.071 6.4 22.2 21.9 

    M6 1 2.2 2 10 and 8 Not tracked 16.8 21.8 20.7 
    """
    payload = parser.parse(sample_text, {"title": "BASS-II Summary Report"})
    assert payload.investigation.combustion_regime == "solid_flame_spread"
    assert len(payload.test_runs) == 2

    m1 = payload.test_runs[0]
    assert m1.run_identifier == "BASS-II-M1"
    assert m1.flame_spread_rate_mm_s == 0.071
    assert math.isclose(m1.si_normalized_parameters["flame_spread_rate_m_s"], 0.000071, abs_tol=1e-8)

    m6 = payload.test_runs[1]
    assert m6.run_identifier == "BASS-II-M6"
    assert m6.flame_spread_rate_mm_s is None
    assert m6.si_normalized_parameters["flame_spread_rate_m_s"] is None

    assert m1.raw_parameters["initial_droplet_diameter_mm"] is None
    assert m1.si_normalized_parameters["droplet_initial_diameter_m"] is None


def test_acme_parser_cld_flames():
    """Tests parsing ACME Coflow Laminar Diffusion flame trials."""
    parser = ACMEParser()
    payload = parser.parse("ACME Text", {"title": "ACME Flight Research"})
    assert payload.investigation.slug == "acme-cld-flame"
    assert payload.investigation.combustion_regime == "laminar_diffusion"
    assert len(payload.test_runs) == 4

    ch4_run = payload.test_runs[0]
    assert ch4_run.run_identifier == "ACME-CLD-CH4-01"
    assert ch4_run.fuel_flow_rate_sccm == 25.0
    flow_si = ch4_run.si_normalized_parameters["fuel_flow_rate_m3_s"]
    assert math.isclose(flow_si, 4.16667e-7, rel_tol=1e-4)

    assert ch4_run.si_normalized_parameters["droplet_initial_diameter_m"] is None


# ==============================================================================
# 6. CONTRACT SCHEMA & PAYLOAD EXPORT TEST
# ==============================================================================

def test_ingestion_payload_conforms_to_contract():
    """Verifies that IngestionPayload.to_contract_dict() conforms to PROJECT.md."""
    parser = ACMEParser()
    payload = parser.parse("Sample", {"title": "ACME Test"})
    contract = payload.to_contract_dict()

    assert "investigation" in contract
    assert "provenance" in contract
    assert "test_runs" in contract
    assert "measurements" in contract

    prov = contract["provenance"]
    assert "sha256_checksum" in prov
    assert len(prov["sha256_checksum"]) == 64
    assert prov["validation_status"] == "VALIDATED"
    assert prov["source_url"].startswith("https://ntrs.nasa.gov/")
