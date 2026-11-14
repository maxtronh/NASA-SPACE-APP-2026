"""FastAPI Endpoints for CCSDS Telemetry Streaming and Daubechies-4 Wavelet Jitter Decomposition.

Exposes:
- GET  /api/v1/telemetry/stream/ccsds     (Server-Sent Events 50 Hz telemetry stream)
- POST /api/v1/telemetry/filter-jitter    (REST endpoint for db4 wavelet acceleration filtering)
- GET  /api/v1/telemetry/wavelet-specs    (REST endpoint for wavelet properties and subbands)
- GET  /api/v1/telemetry/ccsds/specs      (REST endpoint for CCSDS 133.0-B-1 protocol specifications)
- WebSocket /api/v1/telemetry/ws/ccsds    (Interactive WebSocket telemetry stream)
"""

from __future__ import annotations

import asyncio
import json
import math
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse

from backend.app.schemas.stream import (
    CCSDSChannelSpec,
    CCSDSPacketResponse,
    CCSDSSpecsResponse,
    JitterFilterRequest,
    JitterFilterResponse,
    WaveletSpecsResponse,
)
from backend.app.timeseries.ccsds_stream import (
    CCSDS_APID_DEFAULT,
    CCSDS_CHANNEL_KEYS,
    CCSDS_PACKET_SIZE,
    CCSDS_PAYLOAD_SIZE,
    CCSDS_PRIMARY_HEADER_SIZE,
    CCSDS_SECONDARY_HEADER_SIZE,
    CCSDSStreamBuffer,
    generate_cir_telemetry_frame,
    pack_ccsds_packet,
    unpack_ccsds_packet,
)
from backend.app.timeseries.wavelet_filter import filter_g_jitter, get_wavelet_specs

router = APIRouter(prefix="/telemetry", tags=["Telemetry Stream"])


CCSDS_CHANNEL_CATALOG: List[CCSDSChannelSpec] = [
    CCSDSChannelSpec(
        channel_index=0,
        name="chamber_pressure_kpa",
        type="float32",
        unit="kPa",
        description="Chamber total static pressure (101.325 kPa nominal)",
    ),
    CCSDSChannelSpec(
        channel_index=1,
        name="radiant_flux_w",
        type="float32",
        unit="W",
        description="Broadband flame emission radiometer",
    ),
    CCSDSChannelSpec(
        channel_index=2,
        name="ambient_temperature_k",
        type="float32",
        unit="K",
        description="Internal chamber thermocouple ambient temperature",
    ),
    CCSDSChannelSpec(
        channel_index=3,
        name="droplet_diameter_mm",
        type="float32",
        unit="mm",
        description="Instantaneous droplet diameter d(t)",
    ),
    CCSDSChannelSpec(
        channel_index=4,
        name="droplet_diameter_squared_mm2",
        type="float32",
        unit="mm^2",
        description="Square of droplet diameter d^2(t)",
    ),
    CCSDSChannelSpec(
        channel_index=5,
        name="burning_rate_instantaneous_mm2_s",
        type="float32",
        unit="mm^2/s",
        description="Instantaneous burning rate K = -d(d^2)/dt",
    ),
    CCSDSChannelSpec(
        channel_index=6,
        name="acceleration_x_g",
        type="float32",
        unit="g",
        description="X-axis microgravity acceleration vector component",
    ),
    CCSDSChannelSpec(
        channel_index=7,
        name="acceleration_y_g",
        type="float32",
        unit="g",
        description="Y-axis microgravity acceleration vector component",
    ),
    CCSDSChannelSpec(
        channel_index=8,
        name="acceleration_z_g",
        type="float32",
        unit="g",
        description="Z-axis microgravity acceleration vector component",
    ),
    CCSDSChannelSpec(
        channel_index=9,
        name="acceleration_magnitude_g",
        type="float32",
        unit="g",
        description="Euclidean norm of 3-axis acceleration vector",
    ),
    CCSDSChannelSpec(
        channel_index=10,
        name="fuel_flow_sccm",
        type="float32",
        unit="sccm",
        description="Mass flow controller volumetric delivery",
    ),
    CCSDSChannelSpec(
        channel_index=11,
        name="soot_volume_fraction",
        type="float32",
        unit="ppm",
        description="Laser extinction soot volume fraction (NULL when unmeasured)",
    ),
    CCSDSChannelSpec(
        channel_index=12,
        name="flame_spread_rate_mm_s",
        type="float32",
        unit="mm/s",
        description="Axial flame propagation rate",
    ),
]


@router.get("/ccsds/specs", response_model=CCSDSSpecsResponse)
async def get_ccsds_specifications() -> Dict[str, Any]:
    """Returns technical bitfield specifications, headers, and channel layouts for CCSDS 133.0-B-1."""
    return {
        "standard": "CCSDS 133.0-B-1",
        "packet_size_bytes": CCSDS_PACKET_SIZE,
        "primary_header_bytes": CCSDS_PRIMARY_HEADER_SIZE,
        "secondary_header_bytes": CCSDS_SECONDARY_HEADER_SIZE,
        "payload_bytes": CCSDS_PAYLOAD_SIZE,
        "apid_default": CCSDS_APID_DEFAULT,
        "sampling_rate_hz": 50.0,
        "primary_header_bitfields": {
            "word_0": {
                "version_number": "3 bits [15:13] = 000 (CCSDS Version 1)",
                "packet_type": "1 bit [12] = 0 (Telemetry)",
                "secondary_header_flag": "1 bit [11] = 1 (Time Header present)",
                "apid": "11 bits [10:0] = 0x01A0 (416 decimal)",
            },
            "word_1": {
                "sequence_flags": "2 bits [15:14] = 11 (Unsegmented standalone packet)",
                "sequence_count": "14 bits [13:0] (Modulo 16384 rollover counter)",
            },
            "word_2": {
                "packet_data_length": "16 bits [15:0] = 59 (Packet Data Field bytes - 1)",
            },
        },
        "secondary_header_cuc_format": {
            "coarse_time_seconds": "32-bit big-endian unsigned integer (Unix epoch seconds)",
            "fine_time_fraction": "16-bit big-endian unsigned integer (fraction * 65536)",
        },
        "channels": [c.model_dump() for c in CCSDS_CHANNEL_CATALOG],
    }


@router.get("/wavelet-specs", response_model=WaveletSpecsResponse)
async def get_wavelet_filter_specifications(
    sample_rate_hz: float = Query(default=50.0, gt=0.0),
    levels: int = Query(default=5, ge=1, le=10),
    wavelet: str = Query(default="db4"),
) -> Dict[str, Any]:
    """Returns Daubechies filter coefficients, vanishing moments, and dyadic frequency subbands."""
    try:
        specs = get_wavelet_specs(
            sample_rate_hz=sample_rate_hz,
            levels=levels,
            wavelet=wavelet,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    specs["supported_wavelets"] = ["db4", "db2"]
    return specs


@router.post("/filter-jitter", response_model=JitterFilterResponse)
async def filter_microgravity_jitter(request: JitterFilterRequest) -> Dict[str, Any]:
    """Filters acceleration timeseries using pure NumPy Daubechies-4 discrete wavelet transform.

    Separates 1-3 Hz astronaut exercise vibrations and thruster transients from quiescent microgravity.
    """
    effective_levels = request.levels if request.levels is not None else (request.decomposition_levels or 5)
    effective_mode = request.mode if request.mode is not None else (request.filter_mode or "threshold")

    try:
        result = filter_g_jitter(
            accelerations=request.accelerations,
            sample_rate_hz=request.sample_rate_hz,
            levels=effective_levels,
            mode=effective_mode,
            threshold_g=request.threshold_g,
            wavelet=request.wavelet,
            flame_length_scale_m=request.flame_length_scale_m,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get("/stream/ccsds")
async def stream_ccsds_telemetry_sse(
    investigation_slug: str = Query(default="flex-2"),
    run_id: str = Query(default="flex-01"),
    sample_rate_hz: float = Query(default=50.0, ge=1.0, le=100.0),
    jitter_enabled: bool = Query(default=False),
    jitter_amplitude_g: float = Query(default=2.5e-3),
    duration_seconds: float = Query(default=10.0, ge=0.1, le=60.0),
    burst_mode: bool = Query(default=False),
) -> StreamingResponse:
    """Asynchronous Server-Sent Events (SSE) stream delivering 50 Hz CCSDS telemetry frames.

    Simulates ISS CIR Ku-band downlink with optional astronaut treadmill vibration.
    """
    total_frames = max(1, int(duration_seconds * sample_rate_hz))
    dt = 1.0 / sample_rate_hz
    buffer = CCSDSStreamBuffer()
    start_timestamp = 1731600000.0

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            for seq in range(total_frames):
                t = seq * dt
                # Generate physical telemetry state
                telemetry = generate_cir_telemetry_frame(
                    t=t,
                    step=seq,
                    run_id=run_id,
                    jitter_enabled=jitter_enabled,
                    jitter_amplitude_g=jitter_amplitude_g,
                )
                # Pack into CCSDS 133.0-B-1 66-byte packet
                pkt_bytes = pack_ccsds_packet(
                    telemetry=telemetry,
                    sequence_count=seq % 16384,
                    timestamp=start_timestamp + t,
                    apid=CCSDS_APID_DEFAULT,
                )
                # Ingest into sliding window buffer
                unpacked = buffer.ingest_packet(pkt_bytes)

                frame_data = {
                    "investigation_slug": investigation_slug,
                    "run_id": run_id,
                    "frame_index": seq,
                    "total_frames": total_frames,
                    "timestamp": round(start_timestamp + t, 4),
                    "relative_time_s": round(t, 4),
                    "ccsds_packet": unpacked,
                }

                yield f"event: ccsds_telemetry\ndata: {json.dumps(frame_data)}\n\n"

                if not burst_mode:
                    await asyncio.sleep(dt)

            # End of stream event
            final_stats = buffer.get_window_statistics()
            yield f"event: stream_end\ndata: {json.dumps(final_stats)}\n\n"

        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.websocket("/ws/ccsds")
async def ccsds_telemetry_websocket(
    websocket: WebSocket,
    sample_rate_hz: float = Query(default=50.0, ge=1.0, le=100.0),
    jitter_enabled: bool = Query(default=False),
    jitter_amplitude_g: float = Query(default=2.5e-3),
    burst_mode: bool = Query(default=False),
):
    """Bidirectional WebSocket route delivering 50 Hz CCSDS telemetry frames with command control."""
    await websocket.accept()
    buffer = CCSDSStreamBuffer()
    dt = 1.0 / sample_rate_hz
    seq = 0
    t = 0.0
    start_timestamp = 1731600000.0
    is_paused = False

    # Send handshake
    await websocket.send_json({
        "type": "handshake",
        "standard": "CCSDS 133.0-B-1",
        "packet_size_bytes": CCSDS_PACKET_SIZE,
        "sample_rate_hz": sample_rate_hz,
        "status": "STREAMING",
    })

    async def client_listener():
        nonlocal is_paused, jitter_enabled, jitter_amplitude_g
        try:
            while True:
                msg = await websocket.receive_text()
                data = json.loads(msg)
                cmd = data.get("command", "").lower()
                if cmd == "pause":
                    is_paused = True
                    await websocket.send_json({"type": "ack", "command": "pause"})
                elif cmd == "resume":
                    is_paused = False
                    await websocket.send_json({"type": "ack", "command": "resume"})
                elif cmd == "set_jitter":
                    jitter_enabled = bool(data.get("enabled", True))
                    jitter_amplitude_g = float(data.get("amplitude_g", 2.5e-3))
                    await websocket.send_json({"type": "ack", "command": "set_jitter", "jitter_enabled": jitter_enabled})
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass

    listener = asyncio.create_task(client_listener())

    try:
        while True:
            if is_paused:
                await asyncio.sleep(0.05)
                continue

            frame = generate_cir_telemetry_frame(
                t=t,
                step=seq,
                jitter_enabled=jitter_enabled,
                jitter_amplitude_g=jitter_amplitude_g,
            )
            pkt_bytes = pack_ccsds_packet(
                telemetry=frame,
                sequence_count=seq % 16384,
                timestamp=start_timestamp + t,
            )
            unpacked = buffer.ingest_packet(pkt_bytes)

            await websocket.send_json({
                "type": "ccsds_frame",
                "frame_index": seq,
                "relative_time_s": round(t, 4),
                "ccsds_packet": unpacked,
            })

            seq += 1
            t += dt

            if not burst_mode:
                await asyncio.sleep(dt)

    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        listener.cancel()
