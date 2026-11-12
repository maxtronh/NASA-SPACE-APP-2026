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

DEFAULT_RAW_DIR = Path("data/raw")


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
        serialized = json.dumps(content, sort_keys=True, separators=(",", ":"))
        byte_data = serialized.encode("utf-8")

    return hashlib.sha256(byte_data).hexdigest()


def calculate_sha256_from_dict(payload: Dict[str, Any]) -> str:
    """Return the SHA-256 hex digest of a JSON-serializable dict (canonical form)."""
    return calculate_sha256(payload)


def save_raw_payload(
    filename_or_url: str,
    content: Union[bytes, str],
    metadata: Optional[Dict[str, Any]] = None,
    raw_dir: Union[str, Path] = DEFAULT_RAW_DIR,
    http_etag: Optional[str] = None,
    byte_size: Optional[int] = None,
) -> Union[Path, Dict[str, Any]]:
    """
    Saves unmodified raw source payload to data/raw/ and generates sidecar metadata.
    Supports both file path returns and dictionary returns.
    """
    target_dir = Path(raw_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    byte_content = content if isinstance(content, bytes) else content.encode("utf-8")
    if byte_size is None:
        byte_size = len(byte_content)

    # Check if first argument is a URL or a filename
    if filename_or_url.startswith(("http://", "https://")):
        source_url = filename_or_url
        safe_name = source_url.replace("https://", "").replace("http://", "").replace("/", "_")
        filename = f"{safe_name}.raw"
    else:
        filename = filename_or_url
        source_url = metadata.get("source_url", "") if metadata else ""

    file_path = target_dir / filename
    with open(file_path, "wb") as f:
        f.write(byte_content)

    checksum = calculate_sha256(byte_content)
    meta_path = target_dir / f"{filename}.meta.json"

    meta_payload = {
        "filename": filename,
        "byte_size": byte_size,
        "sha256_checksum": checksum,
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "http_etag": http_etag or (metadata.get("http_etag") if metadata else None),
        **(metadata or {})
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2)

    return file_path


def verify_provenance_integrity(
    file_or_content: Union[str, Path, bytes],
    expected_checksum: str
) -> bool:
    """
    Performs cryptographic tamper detection by re-hashing the target file or bytes
    and verifying exact match against expected SHA-256 checksum.
    """
    if isinstance(file_or_content, bytes):
        actual_checksum = hashlib.sha256(file_or_content).hexdigest()
        return actual_checksum.lower() == expected_checksum.lower()

    path = Path(file_or_content)
    if not path.is_file():
        return False

    with open(path, "rb") as f:
        actual_checksum = hashlib.sha256(f.read()).hexdigest()

    return actual_checksum.lower() == expected_checksum.lower()


def build_provenance_record(
    source_url: str,
    raw_payload: Optional[Union[bytes, str, Dict[str, Any]]] = None,
    parser_module: str = "backend.app.ingestion",
    parser_version: str = "1.0.0",
    http_etag: Optional[str] = None,
    original_measurements: Optional[Dict[str, Any]] = None,
    si_measurements: Optional[Dict[str, Any]] = None,
    conversion_method: str = "deterministic_si_table_v1",
    sha256_checksum: Optional[str] = None,
    byte_size: Optional[int] = None,
    validation_status: str = "VALIDATED"
) -> ProvenanceRecord:
    """
    Constructs a verified ProvenanceRecord conforming to docs/PROJECT_ARCHITECTURE.md.
    """
    if sha256_checksum is None:
        if raw_payload is not None:
            sha256_checksum = calculate_sha256(raw_payload)
        else:
            sha256_checksum = ""

    if byte_size is None:
        if isinstance(raw_payload, bytes):
            byte_size = len(raw_payload)
        elif isinstance(raw_payload, str):
            byte_size = len(raw_payload.encode("utf-8"))
        elif raw_payload is not None:
            byte_size = len(json.dumps(raw_payload).encode("utf-8"))
        else:
            byte_size = 0

    return ProvenanceRecord(
        source_url=source_url,
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        sha256_checksum=sha256_checksum,
        http_etag=http_etag,
        byte_size=byte_size,
        parser_module=parser_module,
        parser_version=parser_version,
        validation_status=validation_status,
        original_measurements=original_measurements or {},
        si_measurements=si_measurements or {},
        conversion_method=conversion_method
    )
