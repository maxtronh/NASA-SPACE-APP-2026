"""
NASA Microgravity Combustion Data Ingestion Package.
Provides repeatable discovery, fetching, preservation, parsing,
deterministic SI normalization, and cryptographic provenance tracking.
"""

from .models import (
    InvestigationRecord,
    TestRunRecord,
    MeasurementRecord,
    ProvenanceRecord,
    IngestionPayload,
)
from .normalizer import (
    normalize_to_si,
    convert_pressure_to_pa,
    convert_burning_rate_to_m2_s,
    convert_velocity_to_m_s,
    convert_length_to_m,
    convert_flow_rate_to_m3_s,
    convert_temperature_to_kelvin,
    is_null_or_unobserved,
)
from .preserver import (
    calculate_sha256,
    save_raw_payload,
    verify_provenance_integrity,
    build_provenance_record,
)
from .fetcher import NASADataFetcher
from .parsers import (
    BaseFlightParser,
    FLEXParser,
    BASSParser,
    ACMEParser,
)

__all__ = [
    "InvestigationRecord",
    "TestRunRecord",
    "MeasurementRecord",
    "ProvenanceRecord",
    "IngestionPayload",
    "normalize_to_si",
    "convert_pressure_to_pa",
    "convert_burning_rate_to_m2_s",
    "convert_velocity_to_m_s",
    "convert_length_to_m",
    "convert_flow_rate_to_m3_s",
    "convert_temperature_to_kelvin",
    "is_null_or_unobserved",
    "calculate_sha256",
    "save_raw_payload",
    "verify_provenance_integrity",
    "build_provenance_record",
    "NASADataFetcher",
    "BaseFlightParser",
    "FLEXParser",
    "BASSParser",
    "ACMEParser",
]
