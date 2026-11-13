"""Unit tests for Category 1 Upgrades (01, 02, 03, 04).

Upgrade 01: NASA PSI S3 Sync module (backend/app/ingestion/psi_sync.py)
Upgrade 02: NASA-STD-6001B Flammability Validation Rules engine (backend/app/services/flammability_rules.py)
Upgrade 03: Cool Flames Analysis Module (backend/app/ml/cool_flames.py)
Upgrade 04: Drop Tower Facility Reference Dataset (backend/app/ingestion/drop_tower.py)

Strict compliance:
- Non-zero NULL preservation (missing values are None, never 0.0)
- Zero data fabrication
"""

import pytest
from pathlib import Path

from backend.app.ingestion.psi_sync import (
    AUTHENTIC_PSI_DATASETS,
    PSIDatasetRecord,
    PSIS3FileRecord,
    PSIS3SyncClient,
)
from backend.app.services.flammability_rules import (
    FlammabilityComplianceReport,
    FlammabilityRulesEngine,
    RuleEvaluation,
)
from backend.app.ml.cool_flames import (
    CoolFlamesAnalyzer,
    TwoStageExtinctionProfile,
)
from backend.app.ingestion.drop_tower import (
    DROP_TOWER_FACILITIES,
    DropTowerFacility,
    DropTowerService,
    DropTowerTestRun,
)


# ===========================================================================
# UPGRADE 01: NASA PSI S3 Sync Tests
# ===========================================================================


def test_psi_sync_client_list_datasets():
    client = PSIS3SyncClient(enable_network=False)
    datasets = client.list_datasets()
    assert len(datasets) >= 4
    ids = [d.dataset_id for d in datasets]
    assert "psi-flex-2" in ids
    assert "psi-bass-ii" in ids
    assert "psi-acme-cld" in ids
    assert "psi-sofie-gel" in ids


def test_psi_sync_client_null_preservation():
    """Verify strict NULL preservation: unmeasured metadata fields remain None."""
    client = PSIS3SyncClient(enable_network=False)
    sofie = client.get_dataset("psi-sofie-gel")
    assert sofie is not None
    assert sofie.total_test_runs is None  # Strictly None, never 0.0
    assert sofie.files[0].sha256 is None  # Uncomputed hash is None


def test_psi_sync_client_parse_s3_xml():
    xml_sample = """<?xml version="1.0" encoding="UTF-8"?>
    <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
        <Name>nasa-psi</Name>
        <Prefix>combustion/flex-2/</Prefix>
        <Contents>
            <Key>combustion/flex-2/run_01.csv</Key>
            <LastModified>2022-04-12T14:32:00.000Z</LastModified>
            <ETag>&quot;d41d8cd98f00b204e9800998ecf8427e&quot;</ETag>
            <Size>1048576</Size>
        </Contents>
    </ListBucketResult>"""

    client = PSIS3SyncClient(enable_network=False)
    records = client.parse_s3_xml_listing(xml_sample)
    assert len(records) == 1
    rec = records[0]
    assert rec.key == "combustion/flex-2/run_01.csv"
    assert rec.size_bytes == 1048576
    assert rec.etag == "d41d8cd98f00b204e9800998ecf8427e"


def test_psi_sync_client_checksum_verification(tmp_path: Path):
    test_file = tmp_path / "test_artifact.csv"
    test_file.write_text("authentic_nasa_microgravity_telemetry_line_1\n")

    client = PSIS3SyncClient(enable_network=False)
    import hashlib
    actual_hash = hashlib.sha256(test_file.read_bytes()).hexdigest()

    assert client.verify_file_sha256(test_file, actual_hash) is True
    assert client.verify_file_sha256(test_file, "wrong_hash_000000000000") is False


# ===========================================================================
# UPGRADE 02: NASA-STD-6001B Flammability Validation Rules Tests
# ===========================================================================


def test_flammability_rules_pmma_fails_in_artemis_exploration():
    # Artemis atmosphere: 34% O2 > 17.5% LOI -> Test 1 fails
    report = FlammabilityRulesEngine.evaluate(
        material_key="pmma",
        oxygen_percentage=34.0,
        pressure_kpa=56.5,
        thickness_mm=2.0,
    )
    assert report.overall_status == "NON_COMPLIANT"
    assert report.waiver_required is True

    # Rule IDs present
    rule_ids = [r.rule_id for r in report.rules_evaluated]
    assert "NASA-STD-6001B-LOI" in rule_ids
    assert "NASA-STD-6001B-TEST-1" in rule_ids
    assert "NASA-STD-6001B-TEST-7" in rule_ids

    loi_rule = next(r for r in report.rules_evaluated if r.rule_id == "NASA-STD-6001B-LOI")
    assert loi_rule.status == "FAIL"
    assert loi_rule.margin is not None and loi_rule.margin < 0


def test_flammability_rules_nomex_compliant_in_standard_air():
    # Nomex (LOI 29%) in 21% air
    report = FlammabilityRulesEngine.evaluate(
        material_key="nomex",
        oxygen_percentage=21.0,
        pressure_kpa=101.325,
        thickness_mm=1.5,
    )
    assert report.overall_status == "COMPLIANT"
    assert report.waiver_required is False
    test1_rule = next(r for r in report.rules_evaluated if r.rule_id == "NASA-STD-6001B-TEST-1")
    assert test1_rule.status == "PASS"


def test_flammability_rules_validation_errors():
    with pytest.raises(ValueError):
        FlammabilityRulesEngine.evaluate("unknown_alien_material", oxygen_percentage=21.0)
    with pytest.raises(ValueError):
        FlammabilityRulesEngine.evaluate("pmma", oxygen_percentage=-5.0)
    with pytest.raises(ValueError):
        FlammabilityRulesEngine.evaluate("pmma", oxygen_percentage=105.0)
    with pytest.raises(ValueError):
        FlammabilityRulesEngine.evaluate("pmma", pressure_kpa=-10.0)


# ===========================================================================
# UPGRADE 03: Cool Flames Analysis Tests
# ===========================================================================


def test_cool_flames_n_heptane_large_droplet_transition():
    # n-heptane droplet d0 = 2.5 mm in microgravity air -> supports cool flame
    profile = CoolFlamesAnalyzer.analyze_droplet_transition(
        fuel="n-heptane",
        d0_mm=2.5,
        ambient_o2_pct=21.0,
        pressure_kpa=101.325,
    )
    assert profile.has_cool_flame is True
    assert profile.chemical_regime == "two_stage_cool_flame"
    assert profile.hot_burning_rate_k_mm2_s == 0.58
    assert profile.cool_burning_rate_k_mm2_s == 0.28
    assert profile.first_extinction_diameter_mm is not None
    assert profile.second_extinction_diameter_mm is not None
    assert profile.first_extinction_diameter_mm > profile.second_extinction_diameter_mm
    assert profile.hot_flame_temp_k == 1750.0
    assert profile.cool_flame_temp_k == 720.0


def test_cool_flames_n_heptane_small_droplet_burns_single_stage():
    # n-heptane droplet d0 = 1.0 mm (< 1.5 mm threshold) burns single stage
    profile = CoolFlamesAnalyzer.analyze_droplet_transition(
        fuel="n-heptane",
        d0_mm=1.0,
        ambient_o2_pct=21.0,
    )
    assert profile.has_cool_flame is False
    assert profile.chemical_regime == "single_stage_hot"
    assert profile.cool_burning_rate_k_mm2_s is None  # Strictly None
    assert profile.second_extinction_diameter_mm is None


def test_cool_flames_methanol_never_exhibits_cool_flame():
    profile = CoolFlamesAnalyzer.analyze_droplet_transition(
        fuel="methanol",
        d0_mm=3.0,
        ambient_o2_pct=21.0,
    )
    assert profile.has_cool_flame is False
    assert profile.cool_burning_rate_k_mm2_s is None
    assert profile.cool_flame_temp_k is None


def test_cool_flames_unknown_fuel_preserves_null():
    profile = CoolFlamesAnalyzer.analyze_droplet_transition(
        fuel="uncalibrated_exotic_fuel",
        d0_mm=2.0,
    )
    assert profile.has_cool_flame is False
    assert profile.hot_burning_rate_k_mm2_s is None
    assert profile.cool_burning_rate_k_mm2_s is None
    assert profile.hot_flame_temp_k is None


# ===========================================================================
# UPGRADE 04: Drop Tower Facility Reference Dataset Tests
# ===========================================================================


def test_drop_tower_facilities_catalog():
    facs = DropTowerService.list_facilities()
    assert len(facs) == 4
    ids = [f.facility_id for f in facs]
    assert "grc_2_2s" in ids
    assert "grc_5_18s" in ids
    assert "zarm_bremen_drop" in ids
    assert "zarm_bremen_catapult" in ids


def test_drop_tower_grc_2_2s_vacuum_is_none():
    """Verify strict NULL preservation: GRC 2.2s is atmospheric drag shield -> vacuum_pressure is None."""
    fac = DropTowerService.get_facility("grc_2_2s")
    assert fac is not None
    assert fac.vacuum_chamber is False
    assert fac.vacuum_pressure_pa is None  # Strict NULL


def test_drop_tower_comparison_matrix():
    matrix = DropTowerService.get_facility_comparison_matrix()
    assert "grc_2_2s" in matrix
    assert "grc_5_18s" in matrix
    assert "zarm_bremen_catapult" in matrix
    assert matrix["zarm_bremen_catapult"]["duration_s"] == 9.3
    assert matrix["grc_5_18s"]["height_m"] == 132.0


def test_drop_tower_test_runs_null_preservation():
    runs = DropTowerService.list_test_runs(fuel="n-heptane")
    assert len(runs) >= 2
    # Verify strict NULL for unmeasured soot yield in 2.2s run
    run_22 = next(r for r in runs if r.facility_id == "grc_2_2s")
    assert run_22.soot_yield_fraction is None
    assert run_22.extinction_observed is False


# ===========================================================================
# SKEPTICAL REVIEWER ROBUSTNESS & BOUNDARY PROBES
# ===========================================================================


def test_flammability_rules_none_gravity_and_thin_sample():
    """Verify flammability rules withstand None gravity and ultra-thin fuel thickness."""
    report = FlammabilityRulesEngine.evaluate(
        material_key="pmma",
        oxygen_percentage=21.0,
        pressure_kpa=101.325,
        thickness_mm=0.08,
        gravity_level=None,
    )
    assert report is not None
    assert report.gravity_level is None
    assert len(report.rules_evaluated) == 3


def test_cool_flames_boundary_validation():
    """Verify CoolFlamesAnalyzer raises descriptive ValueError on unphysical boundary inputs."""
    with pytest.raises(ValueError, match="strictly positive"):
        CoolFlamesAnalyzer.analyze_droplet_transition(fuel="n-heptane", d0_mm=-1.0)

    with pytest.raises(ValueError, match="strictly positive"):
        CoolFlamesAnalyzer.analyze_droplet_transition(fuel="n-heptane", d0_mm=0.0)

    with pytest.raises(ValueError, match="Ambient oxygen percentage"):
        CoolFlamesAnalyzer.analyze_droplet_transition(fuel="n-heptane", d0_mm=2.0, ambient_o2_pct=-5.0)

    with pytest.raises(ValueError, match="Ambient oxygen percentage"):
        CoolFlamesAnalyzer.analyze_droplet_transition(fuel="n-heptane", d0_mm=2.0, ambient_o2_pct=105.0)

    with pytest.raises(ValueError, match="Chamber pressure"):
        CoolFlamesAnalyzer.analyze_droplet_transition(fuel="n-heptane", d0_mm=2.0, pressure_kpa=-20.0)


def test_psi_sync_s3_xml_continuation_and_prefixes():
    """Verify S3 XML parser correctly extracts continuation tokens and directory prefixes."""
    paginated_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
        <Name>nasa-psi</Name>
        <Prefix>combustion/</Prefix>
        <IsTruncated>true</IsTruncated>
        <NextContinuationToken>1ueGcxLPRx1Tr/XYgQKEA6uYLPyFVdsPtBGL5JJnvFuZk=</NextContinuationToken>
        <CommonPrefixes>
            <Prefix>combustion/flex-2/</Prefix>
        </CommonPrefixes>
        <CommonPrefixes>
            <Prefix>combustion/bass-ii/</Prefix>
        </CommonPrefixes>
        <Contents>
            <Key>combustion/index.json</Key>
            <LastModified>2023-01-01T00:00:00.000Z</LastModified>
            <ETag>&quot;5d41402abc4b2a76b9719d911017c592&quot;</ETag>
            <Size>2048</Size>
        </Contents>
    </ListBucketResult>"""

    client = PSIS3SyncClient(enable_network=False)
    records = client.parse_s3_xml_listing(paginated_xml)
    assert len(records) == 1
    assert records[0].key == "combustion/index.json"

    meta = client.last_metadata
    assert meta is not None
    assert meta.is_truncated is True
    assert meta.next_continuation_token == "1ueGcxLPRx1Tr/XYgQKEA6uYLPyFVdsPtBGL5JJnvFuZk="
    assert "combustion/flex-2/" in meta.common_prefixes
    assert "combustion/bass-ii/" in meta.common_prefixes

