"""
WebSocket endpoint for real-time sensor telemetry streaming from Parquet flight archives.
Supports configurable playback rates (1x, 2x, 5x, 10x), play/pause/seek controls,
and strict non-zero NULL preservation for authentic NASA microgravity flight sensor readings.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
import pyarrow.parquet as pq

from backend.app.core.logging import logger
from backend.app.timeseries.storage import TimeseriesStorageManager

router = APIRouter(tags=["telemetry-stream"])


def find_parquet_for_run(run_identifier: str, slug: str | None = None) -> tuple[str, Path] | None:
    """Finds the Parquet file and investigation slug for a given run identifier."""
    base_dir = Path("data/timeseries")
    if not base_dir.exists():
        return None

    clean_run = run_identifier.strip()
    if clean_run.endswith(".parquet"):
        clean_run = clean_run[:-8]

    if slug:
        clean_slug = slug.strip().lower()
        candidate = base_dir / clean_slug / f"{clean_run}.parquet"
        if candidate.is_file():
            return clean_slug, candidate

    # Search all slug directories
    for child in base_dir.iterdir():
        if child.is_dir():
            candidate = child / f"{clean_run}.parquet"
            if candidate.is_file():
                return child.name, candidate

    return None


@router.websocket("/ws/timeseries/{run_identifier}")
async def websocket_telemetry_stream(
    websocket: WebSocket,
    run_identifier: str,
    slug: str | None = None,
):
    """
    Real-time streaming WebSocket endpoint for flight sensor timeseries telemetry.
    Streams 100 Hz / 30 Hz flight traces with play/pause/seek and playback rate controls.
    """
    await websocket.accept()

    # Locate telemetry archive
    match = find_parquet_for_run(run_identifier, slug)
    if not match:
        await websocket.send_json({
            "type": "error",
            "code": "RUN_NOT_FOUND",
            "message": f"Telemetry archive for run '{run_identifier}' not found in flight catalog.",
        })
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    investigation_slug, file_path = match

    try:
        table = pq.read_table(file_path)
        records: list[dict[str, Any]] = table.to_pylist()
    except Exception as exc:
        logger.error(f"Failed to read telemetry file {file_path}: {exc}")
        await websocket.send_json({
            "type": "error",
            "code": "FILE_READ_ERROR",
            "message": "Failed to read telemetry parquet data.",
        })
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    total_points = len(records)
    duration_s = records[-1]["time_seconds"] - records[0]["time_seconds"] if total_points > 1 else 0.0

    # Initial metadata handshake
    await websocket.send_json({
        "type": "init",
        "run_identifier": run_identifier,
        "investigation_slug": investigation_slug,
        "total_points": total_points,
        "duration_seconds": round(duration_s, 3),
        "playback_rate": 1.0,
        "status": "ready",
    })

    current_idx = 0
    playback_rate = 1.0
    is_playing = False
    base_interval = 0.033  # ~30 Hz frame rate

    async def handle_client_messages():
        nonlocal current_idx, playback_rate, is_playing
        try:
            while True:
                text = await websocket.receive_text()
                try:
                    msg = json.loads(text)
                    cmd = msg.get("command", "").lower()
                    if cmd == "play":
                        is_playing = True
                        if "rate" in msg:
                            playback_rate = max(0.1, min(20.0, float(msg["rate"])))
                        await websocket.send_json({
                            "type": "ack",
                            "command": "play",
                            "playback_rate": playback_rate,
                            "status": "playing",
                        })
                    elif cmd == "pause":
                        is_playing = False
                        await websocket.send_json({
                            "type": "ack",
                            "command": "pause",
                            "current_index": current_idx,
                            "status": "paused",
                        })
                    elif cmd == "seek":
                        target_time = msg.get("time")
                        target_idx = msg.get("index")
                        if target_idx is not None:
                            current_idx = max(0, min(total_points - 1, int(target_idx)))
                        elif target_time is not None:
                            target_t = float(target_time)
                            # Find closest index
                            current_idx = min(
                                range(total_points),
                                key=lambda i: abs(records[i]["time_seconds"] - target_t),
                            )
                        await websocket.send_json({
                            "type": "ack",
                            "command": "seek",
                            "current_index": current_idx,
                            "time_seconds": records[current_idx]["time_seconds"],
                        })
                    elif cmd == "rate":
                        playback_rate = max(0.1, min(20.0, float(msg.get("rate", 1.0))))
                        await websocket.send_json({
                            "type": "ack",
                            "command": "rate",
                            "playback_rate": playback_rate,
                        })
                    elif cmd == "step":
                        if current_idx < total_points:
                            pt = records[current_idx]
                            await websocket.send_json({
                                "type": "telemetry",
                                "index": current_idx,
                                "time_seconds": pt["time_seconds"],
                                "point": pt,
                            })
                            current_idx += 1
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    await websocket.send_json({"type": "error", "message": f"Invalid command payload: {e}"})
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass

    msg_task = asyncio.create_task(handle_client_messages())

    try:
        while True:
            if is_playing and current_idx < total_points:
                pt = records[current_idx]
                await websocket.send_json({
                    "type": "telemetry",
                    "index": current_idx,
                    "time_seconds": pt["time_seconds"],
                    "point": pt,
                })
                current_idx += 1
                if current_idx >= total_points:
                    is_playing = False
                    await websocket.send_json({
                        "type": "completed",
                        "total_points": total_points,
                        "status": "completed",
                    })

                delay = max(0.001, base_interval / playback_rate)
                await asyncio.sleep(delay)
            else:
                await asyncio.sleep(0.05)
    except (WebSocketDisconnect, asyncio.CancelledError):
        logger.info(f"WebSocket client disconnected for telemetry stream '{run_identifier}'.")
    finally:
        msg_task.cancel()
        try:
            await msg_task
        except (asyncio.CancelledError, WebSocketDisconnect):
            pass
