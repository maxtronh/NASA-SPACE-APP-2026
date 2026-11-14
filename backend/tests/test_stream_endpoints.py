"""
Unit Tests for CCSDS 133.0-B-1 Space Packet Engine and FastAPI Streaming Endpoints.

Verifies:
1. CCSDS Space Packet Protocol 66-byte packet packing and lossless unpacking.
2. Bitfield structure (version, type, secondary flag, APID, sequence flags, sequence count, data length).
3. CCSDS CUC time code conversion with fine fractional sub-millisecond precision.
4. Multi-sensor IEEE-754 payload and Acceptance Rule #4 (preserves None on unmeasured channels).
5. Packet validation error boundaries (APID overflow, sequence count overflow, invalid length, invalid version).
6. CCSDSStreamBuffer ring buffer, sequence tracking, modulo 16384 rollover, and packet loss gap detection.
7. Physical CIR telemetry frame simulation generator (hot vs. cool flame transition, d^2 law, synthetic jitter).
8. REST endpoint GET /api/v1/telemetry/ccsds/specs (status 200, bitfields, channels, sizes).
9. REST endpoint GET /api/v1/telemetry/wavelet-specs (status 200, supported wavelets, subbands, formulas).
10. REST endpoint POST /api/v1/telemetry/filter-jitter (status 200 on valid signals, PAR, SNR, Grashof/Richardson).
11. REST endpoint POST /api/v1/telemetry/filter-jitter HTTP 422 validations (N < 8, NaN/Inf, negative threshold).
12. SSE endpoint GET /api/v1/telemetry/stream/ccsds (status 200, text/event-stream, burst mode execution).
13. WebSocket route /api/v1/telemetry/ws/ccsds (handshake, frame streaming, command controls).
"""

from __future__ import annotations

import json
import math
import struct
from typing import Any, Dict

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.timeseries.ccsds_stream import (
    CCSDS_APID_DEFAULT,
    CCSDS_CHANNEL_KEYS,
    CCSDS_DATA_LENGTH_FIELD,
    CCSDS_PACKET_SIZE,
    CCSDS_PRIMARY_HEADER_SIZE,
    CCSDS_SECONDARY_HEADER_SIZE,
    CCSDS_PAYLOAD_SIZE,
    CCSDSStreamBuffer,
    generate_cir_telemetry_frame,
    pack_ccsds_packet,
    unpack_ccsds_packet,
)


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def sample_telemetry() -> Dict[str, Any]:
    """Sample CIR flight frame with microgravity acceleration."""
    return {
        "chamber_pressure_kpa": 101.325,
        "radiant_flux_w": 18.5,
        "ambient_temperature_k": 298.15,
        "droplet_diameter_mm": 2.15,
        "droplet_diameter_squared_mm2": 4.6225,
        "burning_rate_instantaneous_mm2_s": 0.82,
        "acceleration_x_g": 1.2e-6,
        "acceleration_y_g": -0.8e-6,
        "acceleration_z_g": 0.5e-6,
        "acceleration_magnitude_g": 1.52e-6,
        "fuel_flow_sccm": 12.0,
        "soot_volume_fraction": None,  # Preserves Rule 4: non-zero NULL
        "flame_spread_rate_mm_s": 0.0,
        "status_word": 0x0003,
    }


# ==============================================================================
# SECTION 1: CCSDS 133.0-B-1 PACKET ENCODING & DECODING
# ==============================================================================

class TestCCSDSPacketEncoding:
    """Verifies CCSDS Space Packet 66-byte binary structure and bitfield precision."""

    def test_pack_packet_exact_length_66_bytes(self, sample_telemetry):
        pkt = pack_ccsds_packet(sample_telemetry, sequence_count=1, timestamp=1731600000.0)
        assert isinstance(pkt, bytes)
        assert len(pkt) == CCSDS_PACKET_SIZE, f"Expected {CCSDS_PACKET_SIZE} bytes, got {len(pkt)}"

    def test_primary_header_structure(self, sample_telemetry):
        seq = 1042
        apid = 0x01A0
        pkt = pack_ccsds_packet(sample_telemetry, sequence_count=seq, timestamp=1000.0, apid=apid)

        w0, w1, w2 = struct.unpack(">HHH", pkt[:6])
        version = (w0 >> 13) & 0x07
        pkt_type = (w0 >> 12) & 0x01
        sec_flag = (w0 >> 11) & 0x01
        pkt_apid = w0 & 0x07FF

        seq_flags = (w1 >> 14) & 0x03
        seq_count = w1 & 0x3FFF
        data_len = w2

        assert version == 0
        assert pkt_type == 0
        assert sec_flag == 1
        assert pkt_apid == apid
        assert seq_flags == 3  # Unsegmented
        assert seq_count == seq
        assert data_len == CCSDS_DATA_LENGTH_FIELD  # 59

    def test_secondary_cuc_time_code_precision(self, sample_telemetry):
        timestamp = 1731600123.875  # 0.875 * 65536 = 57344
        pkt = pack_ccsds_packet(sample_telemetry, sequence_count=1, timestamp=timestamp)

        coarse, fine = struct.unpack(">IH", pkt[6:12])
        assert coarse == 1731600123
        assert fine == int(0.875 * 65536)

        unpacked = unpack_ccsds_packet(pkt)
        assert math.isclose(unpacked["secondary_header"]["timestamp_iso"], timestamp, abs_tol=1e-4)

    def test_payload_channels_roundtrip_with_null_preservation(self, sample_telemetry):
        sample_telemetry["soot_volume_fraction"] = None
        sample_telemetry["flame_spread_rate_mm_s"] = 0.55

        pkt = pack_ccsds_packet(sample_telemetry, sequence_count=50, timestamp=500.0)
        unpacked = unpack_ccsds_packet(pkt)

        payload = unpacked["payload"]
        assert math.isclose(payload["chamber_pressure_kpa"], 101.325, rel_tol=1e-5)
        assert math.isclose(payload["radiant_flux_w"], 18.5, rel_tol=1e-5)
        assert math.isclose(payload["ambient_temperature_k"], 298.15, rel_tol=1e-5)
        assert math.isclose(payload["droplet_diameter_mm"], 2.15, rel_tol=1e-5)
        assert math.isclose(payload["acceleration_magnitude_g"], 1.52e-6, rel_tol=1e-5)
        assert math.isclose(payload["flame_spread_rate_mm_s"], 0.55, rel_tol=1e-5)

        # Strict Rule #4 verification: soot must be None, NOT 0.0
        assert payload["soot_volume_fraction"] is None
        assert unpacked["status_word"] == 0x0003

    def test_packet_hex_serialization(self, sample_telemetry):
        pkt = pack_ccsds_packet(sample_telemetry, sequence_count=1, timestamp=100.0)
        unpacked = unpack_ccsds_packet(pkt)
        assert "packet_hex" in unpacked
        assert len(unpacked["packet_hex"]) == 132  # 66 bytes * 2 hex chars
        assert bytes.fromhex(unpacked["packet_hex"]) == pkt

    def test_pack_validation_apid_out_of_range(self, sample_telemetry):
        with pytest.raises(ValueError, match="APID"):
            pack_ccsds_packet(sample_telemetry, sequence_count=0, timestamp=0.0, apid=2048)

        with pytest.raises(ValueError, match="APID"):
            pack_ccsds_packet(sample_telemetry, sequence_count=0, timestamp=0.0, apid=-1)

    def test_pack_validation_sequence_count_out_of_range(self, sample_telemetry):
        with pytest.raises(ValueError, match="Sequence count"):
            pack_ccsds_packet(sample_telemetry, sequence_count=16384, timestamp=0.0)

        with pytest.raises(ValueError, match="Sequence count"):
            pack_ccsds_packet(sample_telemetry, sequence_count=-1, timestamp=0.0)

    def test_unpack_validation_truncated_or_oversized(self):
        with pytest.raises(ValueError, match="66 bytes"):
            unpack_ccsds_packet(b"\x00" * 65)

        with pytest.raises(ValueError, match="66 bytes"):
            unpack_ccsds_packet(b"\x00" * 67)

    def test_unpack_validation_invalid_version(self, sample_telemetry):
        pkt = bytearray(pack_ccsds_packet(sample_telemetry, sequence_count=0, timestamp=0.0))
        # Modify version bits [15:13] in first word to version 1 (001 -> 0x20)
        pkt[0] = pkt[0] | 0x20
        with pytest.raises(ValueError, match="Invalid CCSDS version"):
            unpack_ccsds_packet(bytes(pkt))


# ==============================================================================
# SECTION 2: RING BUFFER & PACKET LOSS DETECTION
# ==============================================================================

class TestCCSDSStreamBuffer:
    """Verifies sequence tracking, modulo 16384 rollover, and packet loss detection."""

    def test_ingest_consecutive_nominal_packets(self, sample_telemetry):
        buf = CCSDSStreamBuffer(max_size=100)
        for seq in range(10):
            pkt = pack_ccsds_packet(sample_telemetry, sequence_count=seq, timestamp=float(seq))
            result = buf.ingest_packet(pkt)
            assert result["packet_loss_detected"] is False
            assert result["lost_packets_in_transition"] == 0
            assert result["cumulative_lost_packets"] == 0

        stats = buf.get_window_statistics()
        assert stats["total_packets_received"] == 10
        assert stats["lost_packets_count"] == 0
        assert stats["packet_loss_percent"] == 0.0
        assert stats["current_window_length"] == 10

    def test_modulo_16384_rollover_no_loss(self, sample_telemetry):
        buf = CCSDSStreamBuffer(max_size=100)
        pkt_16383 = pack_ccsds_packet(sample_telemetry, sequence_count=16383, timestamp=100.0)
        pkt_0 = pack_ccsds_packet(sample_telemetry, sequence_count=0, timestamp=100.02)

        res1 = buf.ingest_packet(pkt_16383)
        res2 = buf.ingest_packet(pkt_0)

        assert res1["packet_loss_detected"] is False
        assert res2["packet_loss_detected"] is False
        assert res2["lost_packets_in_transition"] == 0
        assert buf.lost_packets_count == 0

    def test_sequence_gap_packet_loss_detection(self, sample_telemetry):
        buf = CCSDSStreamBuffer(max_size=100)
        # Sequence 100
        pkt1 = pack_ccsds_packet(sample_telemetry, sequence_count=100, timestamp=10.0)
        buf.ingest_packet(pkt1)

        # Gap: Sequence 105 (4 packets dropped: 101, 102, 103, 104)
        pkt2 = pack_ccsds_packet(sample_telemetry, sequence_count=105, timestamp=10.1)
        res2 = buf.ingest_packet(pkt2)

        assert res2["packet_loss_detected"] is True
        assert res2["lost_packets_in_transition"] == 4
        assert res2["cumulative_lost_packets"] == 4
        assert buf.lost_packets_count == 4

        # Next packet nominal: Sequence 106
        pkt3 = pack_ccsds_packet(sample_telemetry, sequence_count=106, timestamp=10.12)
        res3 = buf.ingest_packet(pkt3)
        assert res3["packet_loss_detected"] is False
        assert res3["lost_packets_in_transition"] == 0
        assert res3["cumulative_lost_packets"] == 4

        stats = buf.get_window_statistics()
        assert stats["total_packets_received"] == 3
        assert stats["lost_packets_count"] == 4
        # Total expected = 3 + 4 = 7; loss percent = (4 / 7) * 100 = 57.1429%
        assert math.isclose(stats["packet_loss_percent"], (4.0 / 7.0) * 100.0, rel_tol=1e-3)

    def test_ring_buffer_eviction_max_size(self, sample_telemetry):
        buf = CCSDSStreamBuffer(max_size=5)
        for seq in range(12):
            pkt = pack_ccsds_packet(sample_telemetry, sequence_count=seq, timestamp=float(seq))
            buf.ingest_packet(pkt)

        assert len(buf.buffer) == 5
        stats = buf.get_window_statistics()
        assert stats["current_window_length"] == 5
        assert stats["total_packets_received"] == 12

    def test_clear_buffer(self, sample_telemetry):
        buf = CCSDSStreamBuffer(max_size=10)
        buf.ingest_packet(pack_ccsds_packet(sample_telemetry, sequence_count=1, timestamp=1.0))
        buf.clear()
        assert len(buf.buffer) == 0
        assert buf.last_sequence_count is None
        assert buf.total_packets_received == 0
        assert buf.lost_packets_count == 0


# ==============================================================================
# SECTION 3: CIR FLIGHT TELEMETRY FRAME GENERATOR
# ==============================================================================

class TestCIRTelemetryGenerator:
    """Verifies synthetic frame generation reflecting authentic CIR FLEX combustion physics."""

    def test_hot_combustion_phase(self):
        frame = generate_cir_telemetry_frame(t=0.5, step=25, jitter_enabled=False)
        assert frame["ambient_temperature_k"] > 1600.0
        assert frame["radiant_flux_w"] > 15.0
        assert (frame["status_word"] & 0x0001) != 0  # Bit 0 hot combustion
        assert frame["soot_volume_fraction"] is None

    def test_cool_flame_transition_phase(self):
        frame = generate_cir_telemetry_frame(t=3.0, step=150, jitter_enabled=False)
        assert 700.0 <= frame["ambient_temperature_k"] <= 730.0
        assert frame["radiant_flux_w"] < 0.50
        assert (frame["status_word"] & 0x0002) != 0  # Bit 1 cool flame active
        assert (frame["status_word"] & 0x0004) != 0  # Bit 2 hot flame extinguished

    def test_droplet_diameter_d2_law_decay(self):
        f0 = generate_cir_telemetry_frame(t=0.0)
        f1 = generate_cir_telemetry_frame(t=1.0)
        f2 = generate_cir_telemetry_frame(t=2.0)

        assert f0["droplet_diameter_squared_mm2"] > f1["droplet_diameter_squared_mm2"] > f2["droplet_diameter_squared_mm2"]
        assert f0["droplet_diameter_mm"] > f1["droplet_diameter_mm"] > f2["droplet_diameter_mm"]

    def test_jitter_injection_toggle(self):
        f_clean = generate_cir_telemetry_frame(t=1.0, jitter_enabled=False)
        f_jitter = generate_cir_telemetry_frame(t=1.0, jitter_enabled=True, jitter_amplitude_g=3.0e-3)

        assert (f_clean["status_word"] & 0x0008) == 0
        assert (f_jitter["status_word"] & 0x0008) != 0
        assert f_jitter["acceleration_magnitude_g"] > f_clean["acceleration_magnitude_g"] * 10.0


# ==============================================================================
# SECTION 4: REST & SSE ENDPOINTS
# ==============================================================================

class TestStreamEndpoints:
    """Verifies FastAPI REST endpoints and SSE stream responses."""

    def test_get_ccsds_specs(self, client: TestClient):
        res = client.get("/api/v1/telemetry/ccsds/specs")
        assert res.status_code == 200
        data = res.json()
        assert data["standard"] == "CCSDS 133.0-B-1"
        assert data["packet_size_bytes"] == 66
        assert data["primary_header_bytes"] == 6
        assert data["secondary_header_bytes"] == 6
        assert data["payload_bytes"] == 54
        assert data["apid_default"] == 0x01A0
        assert len(data["channels"]) == 13

    def test_get_wavelet_specs(self, client: TestClient):
        res = client.get("/api/v1/telemetry/wavelet-specs?sample_rate_hz=50.0&levels=5&wavelet=db4")
        assert res.status_code == 200
        data = res.json()
        assert data["wavelet"] == "db4"
        assert "db4" in data["supported_wavelets"]
        assert "db2" in data["supported_wavelets"]
        assert data["taps"] == 8
        assert data["vanishing_moments"] == 4
        assert len(data["frequency_subbands"]) == 6
        assert "grashof_number" in data["physical_formulas"]

    def test_post_filter_jitter_nominal(self, client: TestClient):
        sample_rate = 50.0
        t = np.arange(0, 4.0, 1.0 / sample_rate)
        quiescent = 1.0e-6 * np.ones_like(t)
        jitter = 2.5e-3 * np.sin(2.0 * np.pi * 1.8 * t)
        noisy = quiescent + jitter

        payload = {
            "accelerations": noisy.tolist(),
            "sample_rate_hz": 50.0,
            "levels": 5,
            "threshold_g": 1.0e-4,
            "mode": "threshold",
        }
        res = client.post("/api/v1/telemetry/filter-jitter", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert len(data["filtered_accelerations"]) == len(noisy)
        assert data["peak_acceleration_reduction_percent"] > 75.0
        assert data["snr_improvement_db"] > 18.0
        assert data["buoyant_perturbation_flag"] is True
        assert data["raw_grashof_peak"] > data["filtered_grashof_peak"]

    def test_post_filter_jitter_modes(self, client: TestClient):
        t = np.arange(0, 2.0, 0.02)
        signal = (1.0e-6 + 2.0e-3 * np.sin(2.0 * np.pi * 1.8 * t)).tolist()

        # Pure approx mode
        res1 = client.post(
            "/api/v1/telemetry/filter-jitter",
            json={"accelerations": signal, "filter_mode": "pure_approx", "decomposition_levels": 4},
        )
        assert res1.status_code == 200
        assert res1.json()["filter_mode"] == "pure_approx"

        # Band stop mode
        res2 = client.post(
            "/api/v1/telemetry/filter-jitter",
            json={"accelerations": signal, "mode": "band_stop"},
        )
        assert res2.status_code == 200
        assert res2.json()["filter_mode"] == "band_stop"

    def test_post_filter_jitter_validation_short_signal_422(self, client: TestClient):
        res = client.post(
            "/api/v1/telemetry/filter-jitter",
            json={"accelerations": [1e-6, 2e-6, 3e-6, 4e-6]},
        )
        assert res.status_code == 422
        assert "at least 8 samples" in res.text

    def test_post_filter_jitter_validation_nan_array_422(self, client: TestClient):
        # Test non-numeric string element rejected with HTTP 422
        res1 = client.post(
            "/api/v1/telemetry/filter-jitter",
            json={"accelerations": ["not-a-number", 1e-6, 2e-6, 3e-6, 4e-6, 5e-6, 6e-6, 7e-6]},
        )
        assert res1.status_code == 422

        # Test null element in JSON rejected with HTTP 422
        res2 = client.post(
            "/api/v1/telemetry/filter-jitter",
            content=b'{"accelerations": [1e-6, null, 2e-6, 3e-6, 4e-6, 5e-6, 6e-6, 7e-6]}',
            headers={"Content-Type": "application/json"},
        )
        assert res2.status_code == 422

    def test_post_filter_jitter_validation_negative_threshold_422(self, client: TestClient):
        res = client.post(
            "/api/v1/telemetry/filter-jitter",
            json={"accelerations": [1e-6] * 16, "threshold_g": -0.001},
        )
        assert res.status_code == 422

    def test_get_stream_ccsds_sse_burst_mode(self, client: TestClient):
        res = client.get("/api/v1/telemetry/stream/ccsds?burst_mode=true&duration_seconds=0.2&sample_rate_hz=50.0")
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("content-type", "")

        content = res.text
        assert "event: ccsds_telemetry" in content
        assert "event: stream_end" in content

        # Parse emitted telemetry lines
        lines = [line for line in content.split("\n") if line.startswith("data: ")]
        assert len(lines) >= 10  # 0.2 s * 50 Hz = 10 frames + 1 end stats

        # Validate first telemetry frame JSON
        first_frame_json = json.loads(lines[0].replace("data: ", ""))
        assert first_frame_json["investigation_slug"] == "flex-2"
        assert "ccsds_packet" in first_frame_json
        pkt = first_frame_json["ccsds_packet"]
        assert pkt["header"]["version"] == 0
        assert pkt["header"]["apid"] == 0x01A0
        assert "payload" in pkt
        assert "chamber_pressure_kpa" in pkt["payload"]

    def test_websocket_ccsds_telemetry_flow(self, client: TestClient):
        with client.websocket_connect("/api/v1/telemetry/ws/ccsds?sample_rate_hz=20.0") as ws:
            # Receive handshake
            handshake = ws.receive_json()
            assert handshake["type"] == "handshake"
            assert handshake["standard"] == "CCSDS 133.0-B-1"

            # Receive telemetry frame
            frame1 = ws.receive_json()
            assert frame1["type"] == "ccsds_frame"
            assert "ccsds_packet" in frame1

            # Send pause command
            ws.send_json({"command": "pause"})
            msg = ws.receive_json()
            while msg.get("type") != "ack":
                msg = ws.receive_json()
            assert msg["command"] == "pause"

            # Send resume command
            ws.send_json({"command": "resume"})
            msg = ws.receive_json()
            while msg.get("type") != "ack":
                msg = ws.receive_json()
            assert msg["command"] == "resume"

            # Send set_jitter command
            ws.send_json({"command": "set_jitter", "enabled": True, "amplitude_g": 0.004})
            msg = ws.receive_json()
            while msg.get("type") != "ack":
                msg = ws.receive_json()
            assert msg["command"] == "set_jitter"
            assert msg["jitter_enabled"] is True
