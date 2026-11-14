"""Pydantic schemas for Silent Cool-Flame Rekindling Early Warning System (Upgrade E-11)."""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field, model_validator


class LTCParameters(BaseModel):
    """Low-Temperature Chemistry kinetic and flammability parameters for a fuel."""

    fuel: str = Field(..., description="Fuel name / identifier")
    chemical_formula: str = Field(..., description="Chemical formula (e.g. C7H16)")
    supports_ltc: bool = Field(..., description="Whether fuel exhibits low-temperature alkylperoxy chemistry")
    flash_point_k: float = Field(..., description="Closed-cup flash point in Kelvin")
    activation_energy_j_mol: Optional[float] = Field(default=None, description="LTC activation energy in J/mol")
    pre_exponential_s_inv: Optional[float] = Field(default=None, description="LTC pre-exponential frequency factor in s^-1")
    critical_damkohler: float = Field(default=1.0, description="Critical Damköhler bifurcation threshold Da_crit")
    transition_theta: float = Field(default=0.20, description="Logistic sigmoid scale parameter theta")
    ntc_temperature_range_k: Optional[tuple[float, float]] = Field(default=None, description="Negative Temperature Coefficient range (T_min, T_max) in K")


class RekindleWarningRequest(BaseModel):
    """Request payload to evaluate instantaneous cool-flame rekindling hazard."""

    fuel: str = Field(default="n-heptane", description="Fuel identifier (e.g. 'n-heptane', 'n-octane', 'n-decane')")
    fuel_temperature_k: float = Field(default=720.0, ge=100.0, le=3000.0, description="Droplet core or flame zone temperature in Kelvin")
    ventilation_velocity_m_s: float = Field(default=0.05, ge=0.001, le=10.0, description="Forced cabin air ventilation velocity in m/s")
    characteristic_length_m: float = Field(default=0.003, ge=0.0001, le=0.5, description="Droplet diameter or characteristic length in meters")
    ambient_o2_percentage: float = Field(default=21.0, ge=1.0, le=100.0, description="Ambient oxygen volume %")
    chamber_pressure_kpa: float = Field(default=101.325, ge=10.0, le=500.0, description="Chamber total pressure in kPa")
    test_run_id: Optional[str] = Field(default=None, description="Optional telemetry run identifier")


class RekindleWarningResponse(BaseModel):
    """Comprehensive rekindling hazard assessment for single flight/laboratory state."""

    test_run_id: Optional[str] = None
    fuel: str
    fuel_formula: str
    supports_ltc: bool
    fuel_temperature_k: float
    flash_point_k: float
    above_flash_point: bool
    ventilation_velocity_m_s: float
    characteristic_length_m: float
    residence_time_s: float
    chemical_timescale_s: Optional[float] = None
    damkohler_cool: float
    damkohler_crit: float
    rekindle_probability: float
    risk_classification: str  # INERT, MONITOR, REKINDLE_WARNING, CRITICAL_REKINDLE_HAZARD
    critical_ventilation_velocity_m_s: float
    ltc_parameters: LTCParameters
    advisory_message: str


class ExtinctionAssessment(BaseModel):
    """Time-indexed assessment of cool-flame activity and rekindling hazard."""

    timestamp_s: float
    temperature_k: float
    radiometer_mw: Optional[float] = None
    damkohler_cool: float
    rekindle_probability: float
    risk_classification: str
    cool_flame_active: bool


class CoolFlameStreamMonitorRequest(BaseModel):
    """Request payload to monitor a time-series stream for silent cool-flame persistence."""

    test_run_id: str = Field(..., description="Telemetry run identifier (e.g. 'FLEX-01-HEPTANE')")
    fuel: str = Field(default="n-heptane", description="Fuel identifier")
    timestamps: list[float] = Field(..., min_length=2, description="Monotonically increasing timestamps in seconds")
    temperatures_k: list[float] = Field(..., min_length=2, description="Droplet core / flame temperatures in Kelvin")
    radiometer_mw: Optional[list[float]] = Field(default=None, description="Broadband flame luminosity radiometer in mW")
    ventilation_velocity_m_s: float = Field(default=0.05, ge=0.001, le=10.0, description="Ventilation airspeed in m/s")
    characteristic_length_m: float = Field(default=0.003, ge=0.0001, le=0.5, description="Droplet diameter in meters")

    @model_validator(mode="after")
    def validate_stream_lengths(self) -> CoolFlameStreamMonitorRequest:
        if len(self.timestamps) != len(self.temperatures_k):
            raise ValueError(
                f"Array length mismatch: timestamps has {len(self.timestamps)} elements but temperatures_k has {len(self.temperatures_k)} elements."
            )
        if self.radiometer_mw is not None and len(self.radiometer_mw) != len(self.timestamps):
            raise ValueError(
                f"Array length mismatch: radiometer_mw has {len(self.radiometer_mw)} elements but timestamps has {len(self.timestamps)} elements."
            )
        return self


class CoolFlameStreamMonitorResponse(BaseModel):
    """Telemetry stream analysis result detailing hot extinction and silent rekindling hazard."""

    test_run_id: str
    fuel: str
    hot_flame_extinction_detected: bool
    hot_flame_extinction_timestamp_s: Optional[float] = None
    cool_flame_active: bool
    current_rekindle_probability: float
    peak_rekindle_probability: float
    current_risk_classification: str
    peak_risk_classification: str
    critical_ventilation_velocity_m_s: float
    timeline_assessments: list[ExtinctionAssessment]
    safety_status: str
