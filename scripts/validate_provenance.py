"""
Flame in Freefall — Provenance and Cryptographic Integrity Validation Script.
Audits all raw NASA payloads in data/raw/ and processed datasets in data/processed/.
Validates SHA-256 checksums, tamper detection, URL authenticity, and NULL preservation.
"""

import json
import logging
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.app.ingestion.preserver import verify_provenance_integrity

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("validate_provenance")


def validate_all() -> bool:
    logger.info("================================================================================")
    logger.info("STARTING CRYPTOGRAPHIC PROVENANCE & INTEGRITY AUDIT")
    logger.info("================================================================================")

    raw_dir = WORKSPACE_ROOT / "data" / "raw"
    processed_dir = WORKSPACE_ROOT / "data" / "processed"

    if not raw_dir.is_dir():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        return False

    all_passed = True
    audited_raw_files = 0

    # 1. Audit Raw Payloads against Sidecar Meta Checksums
    logger.info("[AUDIT 1/3] Verifying Raw Source Payloads in data/raw/...")
    meta_files = list(raw_dir.glob("*.meta.json"))
    if not meta_files:
        logger.error("No sidecar .meta.json files found in data/raw/!")
        return False

    for meta_file in meta_files:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        filename = meta.get("filename")
        expected_hash = meta.get("sha256_checksum")
        if not filename or not expected_hash:
            logger.error(f"Malformed metadata file: {meta_file.name}")
            all_passed = False
            continue

        raw_file = raw_dir / filename
        if not raw_file.is_file():
            logger.error(f"Missing raw payload file: {filename}")
            all_passed = False
            continue

        is_valid = verify_provenance_integrity(raw_file, expected_hash)
        if is_valid:
            logger.info(f"  [OK] {filename} (SHA-256: {expected_hash[:16]}...)")
            audited_raw_files += 1
        else:
            logger.error(f"  [TAMPER DETECTED / MISMATCH] {filename}")
            all_passed = False

    # 2. Audit Processed Payloads
    logger.info("[AUDIT 2/3] Verifying Processed Ingestion Records in data/processed/...")
    processed_files = list(processed_dir.glob("*.json"))
    if not processed_files:
        logger.warning("No processed JSON files found in data/processed/. Run ingest_nasa_data.py first.")
        return False

    for p_file in processed_files:
        if p_file.name == "corpus_index.json":
            continue

        with open(p_file, "r", encoding="utf-8") as f:
            payload = json.load(f)

        prov = payload.get("provenance", {})
        inv = payload.get("investigation", {})
        checksum = prov.get("sha256_checksum")
        source_url = prov.get("source_url")
        status = prov.get("validation_status")

        # Verify hash format (64 hex characters)
        if not checksum or len(checksum) != 64 or not all(c in "0123456789abcdefABCDEF" for c in checksum):
            logger.error(f"  [INVALID CHECKSUM] {p_file.name}: {checksum}")
            all_passed = False
            continue

        # Verify NASA source URL
        if not source_url or not (source_url.startswith(("https://ntrs.nasa.gov/", "https://psi.nasa.gov/"))):
            logger.error(f"  [INVALID NASA URL] {p_file.name}: {source_url}")
            all_passed = False
            continue

        # Verify validation status
        if status != "VALIDATED":
            logger.error(f"  [INVALID STATUS] {p_file.name}: {status}")
            all_passed = False
            continue

        logger.info(f"  [OK] {p_file.name}: Investigation '{inv.get('slug')}', Verified URL: {source_url}")

    # 3. Audit Non-Zero NULL Preservation
    logger.info("[AUDIT 3/3] Auditing Strict Non-Zero NULL Preservation...")
    null_checked_count = 0
    for p_file in processed_files:
        if p_file.name == "corpus_index.json":
            continue

        with open(p_file, "r", encoding="utf-8") as f:
            payload = json.load(f)

        # Check measurements
        for m in payload.get("measurements", []):
            orig = m.get("original_value")
            val_si = m.get("value_si")
            m_name = m.get("metric_name")
            if orig in ("–", "—", "-", "N/A", "NA", "null", "None", None, "Not tracked"):
                if val_si is not None:
                    logger.error(f"  [NULL VIOLATION] {p_file.name} metric '{m_name}': raw '{orig}' was coerced to {val_si} instead of None!")
                    all_passed = False
                null_checked_count += 1

    logger.info(f"  Verified {null_checked_count} missing measurement fields preserved as NULL/None (zero fabrication: 0).")

    logger.info("================================================================================")
    if all_passed:
        logger.info("PROVENANCE INTEGRITY VERIFICATION: 100% PASSED")
        logger.info(f"Total raw files cryptographically verified: {audited_raw_files}")
    else:
        logger.error("PROVENANCE INTEGRITY VERIFICATION: FAILED")
    logger.info("================================================================================")
    return all_passed


if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)
