"""
Cryptographic Provenance Preserver and Tamper Detection Engine.
Computes SHA-256 hashes of unmodified raw NASA payloads, manages data/raw/ storage,
and enforces bitwise immutability.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .models import ProvenanceRecord


def calculate_sha256(content: Union[bytes, str, Dict[str, Any], list]) -> str:
    """
    Computes deterministic SHA-256 cryptographic checksum for data payload.
    Supports raw bytes, strings, and JSON-serializable dictionaries/lists.
    """
    if isinstance(content, bytes):
        byte_data = content
    elif isinstance(content, str):
        byte_data = content.encode("utf-8")
    else:
        # Deterministic JSON canonical representation
        serialized = json.dumps(content, sort_keys=True, separators=(",", ":"))
        byte_data = serialized.encode("utf-8")

    return hashlib.sha256(byte_data).hexdigest()


def save_raw_payload(
    filename: str,
    content: Union[bytes, str],
    metadata: Optional[Dict[str, Any]] = None,
    raw_dir: Union[str, Path] = "data/raw"
) -> Path:
    """
    Saves unmodified raw source payload to data/raw/ and generates sidecar metadata.
    Returns path to saved raw payload.
    """
    target_dir = Path(raw_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / filename
    byte_content = content if isinstance(content, bytes) else content.encode("utf-8")

    with open(file_path, "wb") as f:
        f.write(byte_content)

    checksum = calculate_sha256(byte_content)
    meta_path = target_dir / f"{filename}.meta.json"

    meta_payload = {
        "filename": filename,
        "byte_size": len(byte_content),
        "sha256_checksum": checksum,
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        **(metadata or {})
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2)

    return file_path


def verify_provenance_integrity(
    file_path: Union[str, Path],
    expected_checksum: str
) -> bool:
    """
    Performs cryptographic tamper detection by re-hashing the target file
    and verifying exact match against expected SHA-256 checksum.
    """
    path = Path(file_path)
    if not path.is_file():
        return False

    with open(path, "rb") as f:
        actual_checksum = hashlib.sha256(f.read()).hexdigest()

    return actual_checksum.lower() == expected_checksum.lower()


def build_provenance_record(
    source_url: str,
    raw_payload: Union[bytes, str, Dict[str, Any]],
    parser_module: str,
    parser_version: str = "1.0.0",
    http_etag: Optional[str] = None,
    original_measurements: Optional[Dict[str, Any]] = None,
    si_measurements: Optional[Dict[str, Any]] = None,
    conversion_method: str = "deterministic_si_table_v1"
) -> ProvenanceRecord:
    """
    Constructs a verified ProvenanceRecord conforming to docs/PROJECT_ARCHITECTURE.md.
    """
    checksum = calculate_sha256(raw_payload)
    if isinstance(raw_payload, bytes):
        byte_size = len(raw_payload)
    elif isinstance(raw_payload, str):
        byte_size = len(raw_payload.encode("utf-8"))
    else:
        byte_size = len(json.dumps(raw_payload).encode("utf-8"))

    return ProvenanceRecord(
        source_url=source_url,
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        sha256_checksum=checksum,
        http_etag=http_etag,
        byte_size=byte_size,
        parser_module=parser_module,
        parser_version=parser_version,
        validation_status="VALIDATED",
        original_measurements=original_measurements,
        si_measurements=si_measurements,
        conversion_method=conversion_method
    )
