"""
Real-Time Flight Telemetry Streaming Service for NASA Microgravity Combustion Archives.
Supports WebSocket streaming, play/pause/seek controls, speed multipliers,
and strict non-zero NULL preservation across multi-channel sensor feeds.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
from backend.app.timeseries.generator import ensure_flight_telemetry_seeded
from backend.app.timeseries.schemas import NUMERIC_SENSOR_METRICS
from backend.app.timeseries.storage import TimeseriesStorageManager


class TelemetrySession:
    """Manages the playback state for an active telemetry streaming connection."""

    def __init__(
        self,
        investigation_slug: str,
        run_id: str,
        frames: List[Dict[str, Any]],
        sample_rate_hz: float = 30.0,
    ):
        self.investigation_slug = investigation_slug
        self.run_id = run_id
        self.frames = frames
        self.total_frames = len(frames)
        self.sample_rate_hz = max(1.0, sample_rate_hz)
        self.current_index = 0
        self.is_paused = False
        self.playback_speed = 1.0  # multiplier: 0.5x, 1.0x, 2.0x, 5.0x
        self.duration_s = (
            frames[-1]["time_seconds"] - frames[0]["time_seconds"]
            if frames
            else 0.0
        )

    def is_finished(self) -> bool:
        return self.current_index >= self.total_frames

    def get_current_frame(self) -> Optional[Dict[str, Any]]:
        if 0 <= self.current_index < self.total_frames:
            return self.frames[self.current_index]
        return None

    def advance(self, count: int = 1) -> List[Dict[str, Any]]:
        """Advances playback by count frames and returns them."""
        if self.is_finished() or self.is_paused:
            return []
        start = self.current_index
        end = min(self.total_frames, self.current_index + count)
        self.current_index = end
        return self.frames[start:end]

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def seek(self, time_seconds: float) -> int:
        """Seeks to the closest frame matching time_seconds. Returns the new index."""
        if not self.frames:
            self.current_index = 0
            return 0

        # Binary or linear search for closest time_seconds
        closest_idx = 0
        min_diff = float("inf")
        for i, f in enumerate(self.frames):
            diff = abs(f["time_seconds"] - time_seconds)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i
            elif diff > min_diff:
                # Times are monotonically increasing; we can break early
                break

        self.current_index = closest_idx
        return closest_idx

    def set_speed(self, speed: float) -> float:
        """Sets playback speed multiplier, clamped between 0.1 and 20.0."""
        self.playback_speed = max(0.1, min(20.0, float(speed)))
        return self.playback_speed

    def get_status(self) -> Dict[str, Any]:
        curr = self.get_current_frame()
        return {
            "investigation_slug": self.investigation_slug,
            "run_id": self.run_id,
            "total_frames": self.total_frames,
            "current_index": self.current_index,
            "current_time_s": curr["time_seconds"] if curr else None,
            "duration_s": round(self.duration_s, 4),
            "sample_rate_hz": self.sample_rate_hz,
            "playback_speed": self.playback_speed,
            "is_paused": self.is_paused,
            "is_finished": self.is_finished(),
        }


class TelemetryStreamService:
    """Service to load and initialize telemetry streaming sessions."""

    def __init__(self, base_dir: Optional[Path | str] = None):
        self.storage = TimeseriesStorageManager(base_dir=base_dir)

    def load_run_telemetry(
        self,
        investigation_slug: str,
        run_identifier: Optional[str] = None,
    ) -> TelemetrySession:
        """
        Loads all sensor frames from the Parquet archive into an active TelemetrySession.
        Strictly preserves NULLs and 0.0 values across all channels.
        """
        ensure_flight_telemetry_seeded()
        safe_slug = investigation_slug.strip().lower()

        slug_dir = self.storage.get_investigation_dir(safe_slug)
        if not slug_dir.exists():
            raise FileNotFoundError(f"Telemetry archive for investigation '{safe_slug}' not found.")

        if run_identifier:
            target_file = slug_dir / f"{run_identifier.strip()}.parquet"
        else:
            files = sorted(slug_dir.glob("*.parquet"))
            if not files:
                raise FileNotFoundError(f"No run parquet files found in '{slug_dir}'.")
            target_file = files[0]

        if not target_file.is_file():
            raise FileNotFoundError(f"Telemetry file '{target_file.name}' not found.")

        actual_run_id = target_file.stem
        conn = duckdb.connect(database=":memory:")
        sql = "SELECT * FROM read_parquet(?) ORDER BY time_seconds"
        df = conn.execute(sql, [target_file.as_posix()]).fetchdf()

        frames: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            time_s = round(float(row["time_seconds"]), 4)
            channels: Dict[str, Optional[float]] = {}
            for metric in NUMERIC_SENSOR_METRICS:
                val = row.get(metric)
                if val is not None and not (isinstance(val, float) and str(val) == "nan"):
                    channels[metric] = round(float(val), 6)
                else:
                    channels[metric] = None  # Strict NULL preservation

            is_ext = row.get("is_extinguished")
            is_ext_val = bool(is_ext) if (is_ext is not None and str(is_ext) != "nan") else None

            frames.append(
                {
                    "time_seconds": time_s,
                    "channels": channels,
                    "is_extinguished": is_ext_val,
                }
            )

        # Estimate sampling rate
        total = len(frames)
        if total > 1:
            dur = frames[-1]["time_seconds"] - frames[0]["time_seconds"]
            hz = round((total - 1) / dur, 2) if dur > 0 else 30.0
        else:
            hz = 30.0

        return TelemetrySession(
            investigation_slug=safe_slug,
            run_id=actual_run_id,
            frames=frames,
            sample_rate_hz=hz,
        )
