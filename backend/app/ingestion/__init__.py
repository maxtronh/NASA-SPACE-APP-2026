"""
NASA Microgravity Combustion Data Ingestion Package.
Provides repeatable discovery, fetching, preservation, parsing,
deterministic SI normalization, and cryptographic provenance tracking.
"""

from .fetcher import NASADataFetcher
from .models import (
    IngestionPayload,
    InvestigationRecord,
    MeasurementRecord,
    ProvenanceRecord,
    TestRunRecord,
)
from .normalizer import (
    convert_burning_rate_to_m2_s,
    convert_flow_rate_to_m3_s,
    convert_length_to_m,
    convert_pressure_to_pa,
    convert_temperature_to_kelvin,
    convert_velocity_to_m_s,
    is_null_or_unobserved,
    normalize_to_si,
)
from .parsers import (
    ACMEParser,
    BaseFlightParser,
    BASSParser,
    FLEXParser,
)
from .psi_sync import (
    PSIDatasetRecord,
    PSIS3FileRecord,
    PSIS3SyncClient,
    S3ListingMetadata,
)
from .drop_tower import (
    DropTowerFacility,
    DropTowerService,
    DropTowerTestRun,
)
from .preserver import (
    build_provenance_record,
    calculate_sha256,
    save_raw_payload,
    verify_provenance_integrity,
)

__all__ = [
    "ACMEParser",
    "BASSParser",
    "BaseFlightParser",
    "DropTowerFacility",
    "DropTowerService",
    "DropTowerTestRun",
    "FLEXParser",
    "IngestionPayload",
    "InvestigationRecord",
    "MeasurementRecord",
    "NASADataFetcher",
    "PSIDatasetRecord",
    "PSIS3FileRecord",
    "PSIS3SyncClient",
    "ProvenanceRecord",
    "S3ListingMetadata",
    "TestRunRecord",
    "build_provenance_record",
    "calculate_sha256",
    "convert_burning_rate_to_m2_s",
    "convert_flow_rate_to_m3_s",
    "convert_length_to_m",
    "convert_pressure_to_pa",
    "convert_temperature_to_kelvin",
    "convert_velocity_to_m_s",
    "is_null_or_unobserved",
    "normalize_to_si",
    "save_raw_payload",
    "verify_provenance_integrity",
]
