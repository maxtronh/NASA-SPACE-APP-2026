"""Pydantic schemas for E-12 Interactive Cabin Fire Suppression & Damper Simulator."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CabinSuppressionRequest(BaseModel):
    """Payload for simulating spacecraft cabin emergency fire suppression actions."""

    fuel: str = Field(
        default="n-heptane",
        description="Fuel or spacecraft material identifier (e.g. 'n-heptane', 'n-octane', 'pmma', 'nomex')",
    )
    initial_fuel_temperature_k: float = Field(
        default=720.0,
        ge=100.0,
        le=3000.0,
        description="Initial fuel or core hot-spot temperature in Kelvin",
    )
    initial_o2_percentage: float = Field(
        default=21.0,
        ge=1.0,
        le=100.0,
        description="Initial cabin ambient oxygen concentration in volume %",
    )
    initial_ventilation_velocity_cm_s: float = Field(
        default=3.0,
        ge=0.0,
        le=100.0,
        description="Initial cabin forced ventilation draft velocity in cm/s",
    )
    chamber_pressure_kpa: float = Field(
        default=101.325,
        ge=10.0,
        le=500.0,
        description="Cabin atmospheric pressure in kPa",
    )
    characteristic_length_m: float = Field(
        default=0.003,
        ge=0.0001,
        le=0.5,
        description="Characteristic fuel droplet or solid sample dimension in meters",
    )
    damper_isolated: bool = Field(
        default=False,
        description="Whether ventilation dampers are isolated to shut down forced airflow",
    )
    chemical_agent_released: bool = Field(
        default=False,
        description="Whether gaseous chemical fire extinguishing agent was discharged",
    )
    chemical_agent_type: str = Field(
        default="FK-5-1-12",
        description="Chemical extinguishing agent formulation ('FK-5-1-12' or 'Halon 1301')",
    )
    n2_flooding_active: bool = Field(
        default=False,
        description="Whether nitrogen chamber flooding is activated for hypobaric dilution",
    )
    n2_target_o2_percentage: float = Field(
        default=9.5,
        ge=0.0,
        le=21.0,
        description="Target cabin oxygen concentration under N2 flooding in volume %",
    )
    simulation_duration_s: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Total duration of transient simulation in seconds",
    )
    time_step_s: float = Field(
        default=0.5,
        ge=0.05,
        le=2.0,
        description="Simulation time discretization step in seconds",
    )
    restart_ventilation_velocity_cm_s: float = Field(
        default=3.0,
        ge=0.0,
        le=100.0,
        description="Cabin ventilation draft velocity upon post-incident ventilation restart in cm/s",
    )


class SuppressionDecayPoint(BaseModel):
    """Discrete transient telemetry point during cabin fire suppression."""

    time_s: float = Field(..., description="Timestamp in seconds from emergency action initiation")
    temperature_k: float = Field(..., description="Fuel core or droplet temperature in Kelvin")
    heat_release_rate_kw: float = Field(..., description="Instantaneous flame heat release rate in kW")
    residual_radical_hrr_w: float = Field(..., description="Residual cool-flame radical pool heat release in Watts")
    o2_percentage: float = Field(..., description="Local cabin oxygen volume %")
    ventilation_velocity_cm_s: float = Field(..., description="Cabin ventilation velocity in cm/s")
    agent_concentration_vol_pct: float = Field(..., description="Chemical extinguishing agent concentration in vol %")
    damkohler_cool: float = Field(..., description="Dynamic cool-flame Damköhler number (Da_cool)")
    rekindle_probability: float = Field(..., description="Instantaneous rekindling probability (P_rekindle)")


class CabinSuppressionResponse(BaseModel):
    """Comprehensive physical response from cabin fire suppression simulation."""

    fuel: str = Field(..., description="Fuel or material name")
    fuel_formula: str = Field(..., description="Chemical or empirical formula")
    actions_applied: list[str] = Field(..., description="List of active emergency suppression actions applied")
    extinction_achieved: bool = Field(..., description="Whether flame extinction was achieved within simulation duration")
    transient_extinction_time_s: float | None = Field(
        default=None,
        description="Time in seconds until flame extinction (None if flame persists)",
    )
    extinction_mechanism: str = Field(..., description="Physical/chemical mechanism responsible for extinction")
    initial_temperature_k: float = Field(..., description="Initial fuel temperature in Kelvin")
    final_temperature_k: float = Field(..., description="Final fuel temperature in Kelvin")
    initial_o2_percentage: float = Field(..., description="Initial cabin oxygen volume %")
    final_o2_percentage: float = Field(..., description="Final cabin oxygen volume %")
    initial_ventilation_velocity_cm_s: float = Field(..., description="Initial ventilation velocity in cm/s")
    final_ventilation_velocity_cm_s: float = Field(..., description="Final ventilation velocity in cm/s")
    initial_radical_heat_release_w: float = Field(..., description="Initial residual radical heat release rate in Watts")
    residual_radical_heat_release_w: float = Field(..., description="Final residual radical heat release rate in Watts")
    damkohler_cool_final: float = Field(..., description="Final dynamic cool-flame Damköhler number")
    damkohler_cool_restart: float = Field(
        ...,
        description="Cool-flame Damköhler number if ventilation is restarted with fresh cabin air",
    )
    rekindle_probability_restart: float = Field(
        ...,
        description="Probability of silent rekindling upon cabin ventilation restart",
    )
    rekindle_risk_level: str = Field(
        ...,
        description="Rekindle risk classification ('INERT', 'MONITOR', 'REKINDLE_WARNING', 'CRITICAL_REKINDLE_HAZARD')",
    )
    safe_to_restart_ventilation: bool = Field(
        ...,
        description="Whether it is safe to restore cabin ventilation without risk of fire rekindling",
    )
    decay_curve: list[SuppressionDecayPoint] = Field(..., description="Time-series decay curve of suppression dynamics")
    safety_advisory: str = Field(..., description="Mission control operational guidance advisory")
    audit_message: str = Field(..., description="Standardized flight flight-controller audit telemetry string")
