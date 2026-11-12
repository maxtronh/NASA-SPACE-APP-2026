"""
Real-Time Flight Telemetry WebSocket and Metadata Router for NASA Microgravity Data.
Provides interactive streaming sessions with pause, resume, seek, and speed controls.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from backend.app.services.telemetry_streamer import TelemetrySession, TelemetryStreamService
from backend.app.timeseries.generator import ensure_flight_telemetry_seeded
from backend.app.timeseries.schemas import NUMERIC_SENSOR_METRICS
from backend.app.timeseries.storage import TimeseriesStorageManager

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


class ChannelMetadata(BaseModel):
    name: str
    si_unit: str
    display_unit: str
    description: str
    applicable_experiments: List[str]


CHANNEL_METADATA_CATALOG: List[ChannelMetadata] = [
    ChannelMetadata(
        name="droplet_diameter_mm",
        si_unit="m",
        display_unit="mm",
        description="Instantaneous droplet outer diameter extracted from high-speed CIR backlit imaging.",
        applicable_experiments=["FLEX", "FLEX-2"],
    ),
    ChannelMetadata(
        name="droplet_diameter_squared_mm2",
        si_unit="m^2",
        display_unit="mm^2",
        description="Classical d^2-law regression square diameter; linear slope yields evaporation/burning rate K.",
        applicable_experiments=["FLEX", "FLEX-2"],
    ),
    ChannelMetadata(
        name="burning_rate_instantaneous_mm2_s",
        si_unit="m^2/s",
        display_unit="mm^2/s",
        description="Time derivative -d(d^2)/dt representing instantaneous burning rate.",
        applicable_experiments=["FLEX", "FLEX-2"],
    ),
    ChannelMetadata(
        name="radiant_flux_w",
        si_unit="W",
        display_unit="W",
        description="Total hemispherical radiometer emission from broadband flame chemiluminescence and soot.",
        applicable_experiments=["FLEX", "FLEX-2", "ACME", "BASS-II"],
    ),
    ChannelMetadata(
        name="chamber_pressure_kpa",
        si_unit="Pa",
        display_unit="kPa",
        description="Hermetic CIR or MSG combustion chamber total static pressure.",
        applicable_experiments=["FLEX", "FLEX-2", "ACME", "BASS-II"],
    ),
    ChannelMetadata(
        name="ambient_temperature_k",
        si_unit="K",
        display_unit="K",
        description="Chamber internal ambient thermocouple sensor reading.",
        applicable_experiments=["FLEX", "FLEX-2", "ACME", "BASS-II"],
    ),
    ChannelMetadata(
        name="flame_spread_rate_mm_s",
        si_unit="m/s",
        display_unit="mm/s",
        description="Rate of pyrolysis front advance along solid polymer fuel slab.",
        applicable_experiments=["BASS-II"],
    ),
    ChannelMetadata(
        name="flame_position_mm",
        si_unit="m",
        display_unit="mm",
        description="Absolute axial position of flame leading edge along sample holder.",
        applicable_experiments=["BASS-II"],
    ),
    ChannelMetadata(
        name="fuel_flow_rate_sccm",
        si_unit="m^3/s",
        display_unit="sccm",
        description="Mass flow controller calibrated volumetric delivery of gaseous fuel to co-flow burner.",
        applicable_experiments=["ACME"],
    ),
    ChannelMetadata(
        name="soot_volume_fraction",
        si_unit="dimensionless",
        display_unit="ppm",
        description="Laser-induced incandescence / line-of-sight attenuation soot volume fraction.",
        applicable_experiments=["ACME"],
    ),
]


@router.get("/channels", response_model=List[ChannelMetadata])
async def list_telemetry_channels() -> List[ChannelMetadata]:
    """Returns recognized sensor channels, SI units, and mission applicability."""
    return CHANNEL_METADATA_CATALOG


@router.get("/runs/{id_or_slug}")
async def list_investigation_runs(id_or_slug: str) -> Dict[str, Any]:
    """Lists available timeseries runs and metadata for an investigation."""
    ensure_flight_telemetry_seeded()
    safe_slug = id_or_slug.strip().lower()
    storage = TimeseriesStorageManager()
    slug_dir = storage.get_investigation_dir(safe_slug)

    if not slug_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation telemetry for '{safe_slug}' not found.",
        )

    files = sorted(slug_dir.glob("*.parquet"))
    runs_info = []
    for f in files:
        runs_info.append(
            {
                "run_id": f.stem,
                "file_size_bytes": f.stat().st_size,
                "sha256": storage.compute_file_checksum(f),
            }
        )

    return {
        "investigation_slug": safe_slug,
        "total_runs": len(runs_info),
        "runs": runs_info,
    }


async def handle_telemetry_streaming(
    websocket: WebSocket,
    id_or_slug: str,
    run_id: Optional[str] = None,
    playback_speed: float = 1.0,
    burst_mode: bool = False,
):
    """
    Core WebSocket streaming loop with bidirectional client command support.
    """
    await websocket.accept()
    stream_service = TelemetryStreamService()

    try:
        session: TelemetrySession = stream_service.load_run_telemetry(
            investigation_slug=id_or_slug,
            run_identifier=run_id,
        )
    except FileNotFoundError as exc:
        await websocket.send_json({"type": "error", "message": str(exc)})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    session.set_speed(playback_speed)

    # Initial handshake frame
    await websocket.send_json(
        {
            "type": "handshake",
            "investigation_slug": session.investigation_slug,
            "run_id": session.run_id,
            "total_frames": session.total_frames,
            "sample_rate_hz": session.sample_rate_hz,
            "duration_s": round(session.duration_s, 4),
            "playback_speed": session.playback_speed,
            "channels": NUMERIC_SENSOR_METRICS,
            "status": "STREAMING",
        }
    )

    # Calculate sleep interval
    base_interval = 1.0 / session.sample_rate_hz

    async def client_listener():
        """Listens for bidirectional control commands from the client."""
        try:
            while True:
                msg_text = await websocket.receive_text()
                try:
                    payload = json.loads(msg_text)
                    cmd = payload.get("command", "").lower()
                    if cmd == "pause":
                        session.pause()
                        await websocket.send_json({"type": "ack", "command": "pause", "state": "PAUSED"})
                    elif cmd == "resume":
                        session.resume()
                        await websocket.send_json({"type": "ack", "command": "resume", "state": "STREAMING"})
                    elif cmd == "seek":
                        target_t = float(payload.get("time_seconds", 0.0))
                        new_idx = session.seek(target_t)
                        await websocket.send_json(
                            {
                                "type": "ack",
                                "command": "seek",
                                "current_index": new_idx,
                                "time_seconds": target_t,
                            }
                        )
                    elif cmd == "set_speed":
                        spd = float(payload.get("speed", 1.0))
                        session.set_speed(spd)
                        await websocket.send_json(
                            {"type": "ack", "command": "set_speed", "playback_speed": session.playback_speed}
                        )
                    elif cmd == "status":
                        await websocket.send_json({"type": "status", **session.get_status()})
                    elif cmd == "step":
                        frames = session.advance(1)
                        if frames:
                            await websocket.send_json(
                                {
                                    "type": "telemetry",
                                    "frame_index": session.current_index - 1,
                                    "frame": frames[0],
                                    "state": "STEP",
                                }
                            )
                except Exception as ex:
                    await websocket.send_json({"type": "error", "message": f"Malformed command: {str(ex)}"})
        except WebSocketDisconnect:
            pass
        except asyncio.CancelledError:
            pass

    listener_task = asyncio.create_task(client_listener())

    try:
        while not session.is_finished():
            if session.is_paused:
                await asyncio.sleep(0.05)
                continue

            frames = session.advance(count=1)
            if frames:
                frame = frames[0]
                await websocket.send_json(
                    {
                        "type": "telemetry",
                        "frame_index": session.current_index - 1,
                        "frame": frame,
                        "state": "STREAMING",
                    }
                )

            if not burst_mode:
                sleep_time = max(0.001, base_interval / session.playback_speed)
                await asyncio.sleep(sleep_time)

        # Send completion signal
        await websocket.send_json(
            {
                "type": "completed",
                "total_frames_sent": session.current_index,
                "duration_s": round(session.duration_s, 4),
                "state": "COMPLETED",
            }
        )
    except WebSocketDisconnect:
        pass
    finally:
        listener_task.cancel()


@router.websocket("/stream/{id_or_slug}")
async def telemetry_stream_websocket(
    websocket: WebSocket,
    id_or_slug: str,
    run_id: Optional[str] = Query(default=None),
    playback_speed: float = Query(default=1.0),
    burst_mode: bool = Query(default=False),
):
    """
    High-frequency WebSocket telemetry stream for a flight investigation.
    """
    await handle_telemetry_streaming(
        websocket=websocket,
        id_or_slug=id_or_slug,
        run_id=run_id,
        playback_speed=playback_speed,
        burst_mode=burst_mode,
    )
