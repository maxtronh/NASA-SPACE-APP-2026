"""
CCSDS 133.0-B-1 Space Packet Protocol Generator, Parser, and Ring Buffer.
Simulates 50 Hz ISS CIR Ku-Band Telemetry Downlink with sliding-window loss detection.

Complies with CCSDS 133.0-B-1 Blue Book specification:
- 6-byte Primary Header (>HHH): Version (3b), Type (1b), Sec Hdr Flag (1b), APID (11b),
  Sequence Flags (2b), Sequence Count (14b), Packet Data Length (16b).
- 6-byte Secondary Header (>IH): CCSDS CUC Time Code (32-bit coarse seconds, 16-bit fine fraction).
- 54-byte Multi-Sensor Payload (>13fH): 13 big-endian IEEE-754 float32 channels + 1 uint16 status word.
Total packet size: exactly 66 bytes (132 hex characters).
Preserves non-zero NULL (IEEE-754 NaN -> None) on missing sensor channels (Acceptance Rule #4).
"""

from __future__ import annotations

import collections
import math
import struct
from typing import Any, Dict, List, Optional

# Standard CCSDS 133.0-B-1 Constants
CCSDS_VERSION = 0
CCSDS_TYPE_TM = 0
CCSDS_SEC_HDR_PRESENT = 1
CCSDS_SEQ_FLAGS_UNSEGMENTED = 3
CCSDS_APID_DEFAULT = 0x01A0  # 416 decimal
CCSDS_PRIMARY_HEADER_SIZE = 6
CCSDS_SECONDARY_HEADER_SIZE = 6
CCSDS_PAYLOAD_SIZE = 54
CCSDS_PACKET_SIZE = 66  # 6 + 6 + 54 = 66 bytes
CCSDS_DATA_LENGTH_FIELD = 59  # (6 + 54) - 1 = 59

CCSDS_CHANNEL_KEYS = [
    "chamber_pressure_kpa",
    "radiant_flux_w",
    "ambient_temperature_k",
    "droplet_diameter_mm",
    "droplet_diameter_squared_mm2",
    "burning_rate_instantaneous_mm2_s",
    "acceleration_x_g",
    "acceleration_y_g",
    "acceleration_z_g",
    "acceleration_magnitude_g",
    "fuel_flow_sccm",
    "soot_volume_fraction",
    "flame_spread_rate_mm_s",
]


def pack_ccsds_packet(
    telemetry: dict[str, Any],
    sequence_count: int,
    timestamp: float,
    apid: int = CCSDS_APID_DEFAULT,
) -> bytes:
    """Packs sensor telemetry into standard 66-byte CCSDS 133.0-B-1 Space Packet.

    Args:
        telemetry: Dictionary containing sensor channel readings and status_word.
        sequence_count: Modulo-16384 packet sequence count (0 to 16383).
        timestamp: Unix epoch timestamp in seconds (with fractional second precision).
        apid: 11-bit Application Process Identifier (0 to 2047, default: 0x01A0).

    Returns:
        66-byte big-endian packed bytes object.

    Raises:
        ValueError: If APID or sequence_count is outside the valid range.
    """
    if apid < 0 or apid > 2047:
        raise ValueError(f"APID {apid} out of range [0, 2047]")
    if sequence_count < 0 or sequence_count > 16383:
        raise ValueError(f"Sequence count {sequence_count} out of range [0, 16383]")

    # Primary Header (6 bytes):
    # Word 0: Version(3b)=0, Type(1b)=0, SecHdr(1b)=1, APID(11b)
    word0 = (CCSDS_VERSION << 13) | (CCSDS_TYPE_TM << 12) | (CCSDS_SEC_HDR_PRESENT << 11) | (apid & 0x07FF)
    # Word 1: SeqFlags(2b)=3, SeqCount(14b)
    word1 = (CCSDS_SEQ_FLAGS_UNSEGMENTED << 14) | (sequence_count & 0x3FFF)
    # Word 2: Packet Data Length = 60 - 1 = 59
    word2 = CCSDS_DATA_LENGTH_FIELD
    primary_hdr = struct.pack(">HHH", word0, word1, word2)

    # Secondary Header (6 bytes CUC time code):
    coarse = int(timestamp)
    fine = int((timestamp - coarse) * 65536.0) & 0xFFFF
    secondary_hdr = struct.pack(">IH", coarse, fine)

    # Payload (54 bytes = 13 float32 + 1 uint16):
    channels = [
        telemetry.get("chamber_pressure_kpa", math.nan),
        telemetry.get("radiant_flux_w", math.nan),
        telemetry.get("ambient_temperature_k", math.nan),
        telemetry.get("droplet_diameter_mm", math.nan),
        telemetry.get("droplet_diameter_squared_mm2", math.nan),
        telemetry.get("burning_rate_instantaneous_mm2_s", math.nan),
        telemetry.get("acceleration_x_g", math.nan),
        telemetry.get("acceleration_y_g", math.nan),
        telemetry.get("acceleration_z_g", math.nan),
        telemetry.get("acceleration_magnitude_g", math.nan),
        telemetry.get("fuel_flow_sccm", math.nan),
        telemetry.get("soot_volume_fraction", math.nan),
        telemetry.get("flame_spread_rate_mm_s", math.nan),
    ]

    # Rule 4: Preserves non-zero NULL by packing None or NaN as IEEE-754 NaN
    cleaned_channels: list[float] = []
    for val in channels:
        if val is None or (isinstance(val, (float, int)) and math.isnan(val)):
            cleaned_channels.append(math.nan)
        else:
            cleaned_channels.append(float(val))

    status_word = int(telemetry.get("status_word", 0)) & 0xFFFF
    payload = struct.pack(">13fH", *cleaned_channels, status_word)

    return primary_hdr + secondary_hdr + payload


def unpack_ccsds_packet(raw_bytes: bytes) -> dict[str, Any]:
    """Unpacks a raw 66-byte CCSDS 133.0-B-1 Space Packet.

    Args:
        raw_bytes: 66-byte binary packet.

    Returns:
        Structured dictionary with header, secondary_header, payload, and status_word.

    Raises:
        ValueError: If packet length is not 66 bytes or version is not 0.
    """
    if len(raw_bytes) != CCSDS_PACKET_SIZE:
        raise ValueError(
            f"CCSDS packet length {len(raw_bytes)} != {CCSDS_PACKET_SIZE} bytes"
        )

    w0, w1, w2 = struct.unpack(">HHH", raw_bytes[0:6])
    version = (w0 >> 13) & 0x07
    if version != CCSDS_VERSION:
        raise ValueError(f"Invalid CCSDS version {version} != {CCSDS_VERSION}")

    pkt_type = (w0 >> 12) & 0x01
    sec_hdr_flag = (w0 >> 11) & 0x01
    apid = w0 & 0x07FF
    seq_flags = (w1 >> 14) & 0x03
    seq_count = w1 & 0x3FFF
    data_length = w2

    coarse, fine = struct.unpack(">IH", raw_bytes[6:12])
    timestamp = coarse + (fine / 65536.0)

    payload_values = struct.unpack(">13fH", raw_bytes[12:66])
    payload: dict[str, Any] = {}
    for key, val in zip(CCSDS_CHANNEL_KEYS, payload_values[:13]):
        payload[key] = None if math.isnan(val) else float(val)

    status_word = payload_values[13]

    return {
        "header": {
            "version": version,
            "packet_type": pkt_type,
            "secondary_header_flag": sec_hdr_flag,
            "apid": apid,
            "sequence_flags": seq_flags,
            "sequence_count": seq_count,
            "packet_data_length": data_length,
        },
        "secondary_header": {
            "coarse_time_s": coarse,
            "fine_time_fraction": fine,
            "timestamp_iso": timestamp,
        },
        "payload": payload,
        "status_word": status_word,
        "packet_hex": raw_bytes.hex().upper(),
    }


class CCSDSStreamBuffer:
    """Sliding-window circular ring buffer with sequence tracking and packet loss detection."""

    def __init__(self, max_size: int = 512):
        self.max_size = max_size
        self.buffer: collections.deque[dict[str, Any]] = collections.deque(maxlen=max_size)
        self.last_sequence_count: Optional[int] = None
        self.total_packets_received: int = 0
        self.lost_packets_count: int = 0

    def ingest_packet(self, packet_bytes: bytes) -> dict[str, Any]:
        """Ingests a 66-byte packet, detects sequence gaps, and updates window buffer.

        Handles modulo 16384 rollover (16383 -> 0).
        """
        unpacked = unpack_ccsds_packet(packet_bytes)
        seq_count = unpacked["header"]["sequence_count"]

        loss_detected = False
        loss_in_transition = 0

        if self.last_sequence_count is not None:
            delta = (seq_count - self.last_sequence_count) % 16384
            if delta > 1:
                loss_in_transition = delta - 1
                self.lost_packets_count += loss_in_transition
                loss_detected = True

        self.last_sequence_count = seq_count
        self.total_packets_received += 1

        unpacked["packet_loss_detected"] = loss_detected
        unpacked["lost_packets_in_transition"] = loss_in_transition
        unpacked["cumulative_lost_packets"] = self.lost_packets_count

        self.buffer.append(unpacked)
        return unpacked

    def get_window_statistics(self) -> dict[str, Any]:
        """Computes transmission statistics over the sliding window."""
        total_expected = self.total_packets_received + self.lost_packets_count
        loss_pct = (
            (self.lost_packets_count / total_expected * 100.0)
            if total_expected > 0
            else 0.0
        )
        return {
            "total_packets_received": self.total_packets_received,
            "lost_packets_count": self.lost_packets_count,
            "packet_loss_percent": round(loss_pct, 4),
            "buffer_capacity": self.max_size,
            "current_window_length": len(self.buffer),
            "last_sequence_count": self.last_sequence_count,
        }

    def clear(self) -> None:
        """Resets the buffer and counters."""
        self.buffer.clear()
        self.last_sequence_count = None
        self.total_packets_received = 0
        self.lost_packets_count = 0


def generate_cir_telemetry_frame(
    t: float,
    step: int = 0,
    run_id: str = "FLEX-01",
    jitter_enabled: bool = False,
    jitter_amplitude_g: float = 2.5e-3,
) -> dict[str, Any]:
    """Generates an authentic 50 Hz CIR telemetry frame simulating microgravity droplet combustion.

    Simulates initial droplet heating, hot flame combustion, radiative extinction transition,
    and cool-flame persistence, with optional 1.8 Hz astronaut exercise vibration.
    """
    p_kpa = 101.325 + 0.05 * math.sin(0.1 * t)

    # Flame temperature & radiometer transition at t = 2.0 s:
    # Hot droplet combustion (T ~ 1700 K, radiometer > 15 W) extinguishing to cool flame (T ~ 720 K, radiometer ~ 0.2 W)
    if t < 2.0:
        temp_k = 1750.0 - 100.0 * t
        rad_w = max(0.5, 25.0 - 10.0 * t)
        status_word = 0x0001  # Bit 0: Ignition / Hot flame active
    else:
        temp_k = max(700.0, 725.0 - 2.0 * (t - 2.0))
        rad_w = max(0.05, 0.35 - 0.02 * (t - 2.0))
        status_word = 0x0002 | 0x0004  # Bit 1: Cool flame active, Bit 2: Hot flame extinguished

    # Droplet d^2 law: d(t) = sqrt(max(0.01, d0^2 - K * t))
    d0 = 2.2  # mm
    k_rate = 0.82  # mm^2/s
    d2 = max(0.01, d0 ** 2 - k_rate * t)
    d = math.sqrt(d2)

    # Microgravity acceleration (quiescent baseline ~ 10^-6 g)
    ax = 1.0e-6 * (1.0 + 0.1 * math.sin(0.05 * t))
    ay = -0.8e-6 * (1.0 + 0.1 * math.cos(0.05 * t))
    az = 0.5e-6 * math.sin(0.02 * t)

    if jitter_enabled:
        status_word |= 0x0008  # Bit 3: Jitter injected
        # 1.8 Hz astronaut treadmill resonance vibration
        jitter = jitter_amplitude_g * math.sin(2.0 * math.pi * 1.8 * t)
        az += jitter

    amag = math.sqrt(ax ** 2 + ay ** 2 + az ** 2)

    return {
        "chamber_pressure_kpa": round(p_kpa, 4),
        "radiant_flux_w": round(rad_w, 4),
        "ambient_temperature_k": round(temp_k, 2),
        "droplet_diameter_mm": round(d, 4),
        "droplet_diameter_squared_mm2": round(d2, 4),
        "burning_rate_instantaneous_mm2_s": k_rate if d > 0.1 else 0.0,
        "acceleration_x_g": ax,
        "acceleration_y_g": ay,
        "acceleration_z_g": az,
        "acceleration_magnitude_g": amag,
        "fuel_flow_sccm": 12.0,
        "soot_volume_fraction": None,  # Preserves Rule 4: non-zero NULL for missing optical channel
        "flame_spread_rate_mm_s": 0.0,
        "status_word": status_word,
    }
