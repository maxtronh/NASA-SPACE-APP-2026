"""Pydantic v2 schemas for CCSDS 133.0-B-1 Telemetry Streaming and Wavelet Jitter Decomposition."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator


class CCSDSPrimaryHeader(BaseModel):
    """CCSDS 133.0-B-1 6-byte Primary Header Bitfield Model."""

    version: int = Field(default=0, description="CCSDS Packet Version Number (3 bits, must be 0)")
    packet_type: int = Field(default=0, description="Packet Type Indicator (1 bit: 0 = TM, 1 = TC)")
    secondary_header_flag: int = Field(default=1, description="Secondary Header Flag (1 bit: 1 = Present)")
    apid: int = Field(default=0x01A0, description="Application Process Identifier (11 bits: 0-2047)")
    sequence_flags: int = Field(default=3, description="Sequence Flags (2 bits: 3 = Unsegmented)")
    sequence_count: int = Field(..., ge=0, le=16383, description="Packet Sequence Count (14 bits: 0-16383)")
    packet_data_length: int = Field(default=59, description="Packet Data Length field: (data_field_bytes - 1)")


class CCSDSSecondaryHeader(BaseModel):
    """CCSDS CUC (CCSDS Unsegmented Code) Time Code 6-byte Header."""

    coarse_time_s: int = Field(..., description="Seconds since epoch (32-bit uint)")
    fine_time_fraction: int = Field(..., description="Fractional seconds (16-bit uint: fine/65536)")
    timestamp_iso: Union[float, str] = Field(..., description="Calculated timestamp (coarse + fine/65536.0)")


class CCSDSTelemetryPayload(BaseModel):
    """Multi-sensor CIR combustion telemetry channel payload (54 bytes).

    Missing or unmeasured channels are preserved strictly as None (Acceptance Rule #4).
    """

    chamber_pressure_kpa: Optional[float] = Field(default=None, description="Hermetic combustion chamber pressure (kPa)")
    radiant_flux_w: Optional[float] = Field(default=None, description="Broadband radiometer emission (W)")
    ambient_temperature_k: Optional[float] = Field(default=None, description="Ambient thermocouple reading (K)")
    droplet_diameter_mm: Optional[float] = Field(default=None, description="Droplet diameter d(t) (mm)")
    droplet_diameter_squared_mm2: Optional[float] = Field(default=None, description="Droplet d^2(t) (mm^2)")
    burning_rate_instantaneous_mm2_s: Optional[float] = Field(default=None, description="Instantaneous burning rate K (mm^2/s)")
    acceleration_x_g: Optional[float] = Field(default=None, description="X-axis microgravity acceleration (g)")
    acceleration_y_g: Optional[float] = Field(default=None, description="Y-axis microgravity acceleration (g)")
    acceleration_z_g: Optional[float] = Field(default=None, description="Z-axis microgravity acceleration (g)")
    acceleration_magnitude_g: Optional[float] = Field(default=None, description="Total acceleration vector norm (g)")
    fuel_flow_sccm: Optional[float] = Field(default=None, description="Mass flow controller delivery (sccm)")
    soot_volume_fraction: Optional[float] = Field(default=None, description="Laser-induced soot volume fraction (ppm)")
    flame_spread_rate_mm_s: Optional[float] = Field(default=None, description="Solid fuel flame spread rate (mm/s)")


class CCSDSPacketResponse(BaseModel):
    """Complete decoded CCSDS space packet model."""

    header: CCSDSPrimaryHeader
    secondary_header: CCSDSSecondaryHeader
    payload: CCSDSTelemetryPayload
    status_word: int = Field(default=0, description="16-bit discrete system status word")
    packet_hex: Optional[str] = Field(default=None, description="Raw 132-character hexadecimal representation")
    packet_loss_detected: Optional[bool] = Field(default=False, description="Flag indicating sequence gap in stream")
    lost_packets_in_transition: Optional[int] = Field(default=0, description="Count of lost packets in this transition")
    cumulative_lost_packets: Optional[int] = Field(default=0, description="Cumulative lost packets count")


class CCSDSChannelSpec(BaseModel):
    """Metadata specification for a CCSDS telemetry sensor channel."""

    channel_index: int
    name: str
    type: str
    unit: str
    description: str


class CCSDSSpecsResponse(BaseModel):
    """Technical specification document for the CCSDS 133.0-B-1 Telemetry Downlink."""

    standard: str = Field(default="CCSDS 133.0-B-1", description="Authoritative standard name")
    packet_size_bytes: int = Field(default=66, description="Total binary packet size")
    primary_header_bytes: int = Field(default=6, description="Primary header size")
    secondary_header_bytes: int = Field(default=6, description="Secondary CUC time header size")
    payload_bytes: int = Field(default=54, description="Multi-sensor payload size")
    apid_default: int = Field(default=0x01A0, description="Default CIR Telemetry APID (416)")
    sampling_rate_hz: float = Field(default=50.0, description="Nominal Ku-band telemetry downlink frequency")
    primary_header_bitfields: Dict[str, Any]
    secondary_header_cuc_format: Dict[str, Any]
    channels: List[CCSDSChannelSpec]


class JitterFilterRequest(BaseModel):
    """Payload to perform Daubechies-4 discrete wavelet jitter filtering on raw acceleration timeseries."""

    accelerations: List[float] = Field(..., description="Raw 1D acceleration measurements in units of g")
    sample_rate_hz: float = Field(default=50.0, gt=0.0, description="Sampling rate in Hertz")
    levels: Optional[int] = Field(default=None, ge=1, description="Decomposition depth (alias for decomposition_levels)")
    decomposition_levels: Optional[int] = Field(default=5, ge=1, description="Dyadic decomposition depth")
    mode: Optional[str] = Field(default=None, description="Filter mode (alias for filter_mode)")
    filter_mode: Optional[str] = Field(default="threshold", description="Filter mode ('threshold', 'pure_approx', 'band_stop')")
    threshold_g: float = Field(default=1.0e-4, gt=0.0, description="Wavelet detail suppression threshold in g")
    wavelet: str = Field(default="db4", description="Wavelet family ('db4' or 'db2')")
    flame_length_scale_m: float = Field(default=0.003, gt=0.0, description="Droplet characteristic length scale in meters")

    @model_validator(mode="after")
    def validate_accelerations_and_parameters(self) -> JitterFilterRequest:
        if len(self.accelerations) < 8:
            raise ValueError("Signal length must be at least 8 samples for db4 wavelet decomposition.")
        for v in self.accelerations:
            if math.isnan(v) or math.isinf(v):
                raise ValueError(
                    "Acceleration signal contains invalid non-numeric or NaN values. "
                    "For missing telemetry, preserve NULL at channel level before filtering."
                )
        return self


class JitterFilterResponse(BaseModel):
    """Filtered microgravity signal, hydrodynamic indices, and wavelet energy spectrum."""

    filtered_accelerations: List[float]
    snr_improvement_db: float
    peak_acceleration_reduction_percent: float
    raw_grashof_peak: float
    filtered_grashof_peak: float
    buoyant_perturbation_flag: bool
    wavelet_power_spectrum: Dict[str, float]
    raw_peak_g: float
    filtered_peak_g: float
    raw_richardson_peak: float
    filtered_richardson_peak: float
    decomposition_levels: int
    wavelet: str
    filter_mode: str


class FrequencySubband(BaseModel):
    """Specification of a dyadic wavelet frequency subband."""

    level: int
    band: str
    type: str
    frequency_low_hz: float
    frequency_high_hz: float
    description: str


class WaveletSpecsResponse(BaseModel):
    """Technical specifications, coefficients, and physical formulas for the wavelet filter."""

    wavelet: str = Field(default="db4")
    supported_wavelets: List[str] = Field(default_factory=lambda: ["db4", "db2"])
    taps: int = Field(default=8)
    vanishing_moments: int = Field(default=4)
    scaling_coefficients_h: List[float]
    wavelet_coefficients_g: List[float]
    sample_rate_hz: float = Field(default=50.0)
    decomposition_levels: int = Field(default=5)
    frequency_subbands: List[FrequencySubband]
    physical_formulas: Dict[str, str]
