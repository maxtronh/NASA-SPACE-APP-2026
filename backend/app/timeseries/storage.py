"""
Parquet Storage Manager for High-Frequency Flight Sensor Telemetry.
Handles Snappy-compressed columnar Parquet files with SHA-256 integrity verification.
"""

import hashlib
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from backend.app.timeseries.schemas import SENSOR_TIMESERIES_SCHEMA


class TimeseriesStorageManager:
    """Manages reading and writing high-frequency sensor timeseries in Apache Parquet format."""

    def __init__(self, base_dir: Path | str | None = None):
        if base_dir is None:
            self.base_dir = Path("data/timeseries")
        else:
            self.base_dir = Path(base_dir)

    def get_investigation_dir(self, investigation_slug: str) -> Path:
        """Returns the directory for a specific investigation slug."""
        return self.base_dir / investigation_slug

    def get_parquet_path(self, investigation_slug: str, run_identifier: str) -> Path:
        """Returns the destination Parquet file path for an experimental run."""
        safe_slug = investigation_slug.strip().lower()
        safe_run = run_identifier.strip()
        return self.base_dir / safe_slug / f"{safe_run}.parquet"

    def run_exists(self, investigation_slug: str, run_identifier: str) -> bool:
        """Checks if a Parquet file exists for the specified run."""
        return self.get_parquet_path(investigation_slug, run_identifier).is_file()

    @staticmethod
    def compute_file_checksum(file_path: Path) -> str:
        """Computes the SHA-256 checksum of the Parquet file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def write_run_parquet(
        self,
        data: pa.Table | list[dict[str, Any]],
        investigation_slug: str,
        run_identifier: str,
        compression: str = "snappy",
    ) -> Path:
        """
        Writes timeseries telemetry to a Snappy-compressed Parquet file.
        Strictly preserves NULL values and schema definitions.
        """
        target_path = self.get_parquet_path(investigation_slug, run_identifier)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, list):
            # Convert list of dictionaries to PyArrow table with strict schema conformance
            table = pa.Table.from_pylist(data, schema=SENSOR_TIMESERIES_SCHEMA)
        elif isinstance(data, pa.Table):
            table = data
        else:
            raise TypeError(f"Unsupported data type for Parquet export: {type(data)}")

        # Write Parquet with Snappy compression and dictionary encoding
        pq.write_table(
            table=table,
            where=target_path,
            compression=compression,
            use_dictionary=True,
            flavor=None,
        )

        return target_path

    def read_parquet_table(
        self,
        investigation_slug: str,
        run_identifier: str,
        columns: list[str] | None = None,
    ) -> pa.Table:
        """Reads a Parquet file into a PyArrow table with optional column projection."""
        target_path = self.get_parquet_path(investigation_slug, run_identifier)
        if not target_path.is_file():
            raise FileNotFoundError(
                f"Timeseries Parquet not found for {investigation_slug}/{run_identifier} at {target_path}"
            )
        return pq.read_table(target_path, columns=columns)

    def list_runs(self, investigation_slug: str | None = None) -> list[dict[str, Any]]:
        """Lists all existing runs stored as Parquet files."""
        if not self.base_dir.exists():
            return []

        runs = []
        if investigation_slug:
            pattern = f"{investigation_slug.strip().lower()}/*.parquet"
        else:
            pattern = "*/*.parquet"

        for p in sorted(self.base_dir.glob(pattern)):
            slug = p.parent.name
            run_id = p.stem
            runs.append(
                {
                    "investigation_slug": slug,
                    "run_identifier": run_id,
                    "file_path": str(p),
                    "byte_size": p.stat().st_size,
                }
            )

        return runs
