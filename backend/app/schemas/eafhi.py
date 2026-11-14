"""Pydantic schemas for Exploration Atmosphere Fire Hazard Index (EAFHI) (Upgrade E-10)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class EAFHICalculateRequest(BaseModel):
    """Request payload to calculate Exploration Atmosphere Fire Hazard Index."""

    material: str = Field(
        default="pmma",
        description="Material identifier ('pmma', 'nomex', 'delrin', 'polycarbonate', 'teflon', 'kevlar')"
    )
    pressure_kpa: float = Field(
        default=56.5,
        ge=10.0,
        le=250.0,
        description="Atmospheric total pressure in kPa (Artemis Gateway baseline = 56.5 kPa)"
    )
    oxygen_percentage: float = Field(
        default=34.0,
        ge=0.0,
        le=100.0,
        description="Oxygen volume percentage (Artemis Gateway baseline = 34.0 %)"
    )
    gravity_level: str = Field(
        default="lunar_gravity (0.16 g)",
        description="Gravitational regime (e.g. 'lunar_gravity (0.16 g)', 'microgravity (~10^-6 g)', 'normal_gravity (1.0 g)')"
    )
    characteristic_length_m: float = Field(
        default=0.05,
        ge=0.001,
        le=1.0,
        description="Sample or flame characteristic length L in meters (default 0.05 m = 5 cm)"
    )
    ventilation_velocity_cm_s: float = Field(
        default=3.0,
        ge=0.0,
        le=50.0,
        description="Forced cabin ventilation flow velocity in cm/s"
    )
    flame_temperature_k: float = Field(
        default=1800.0,
        ge=600.0,
        le=3000.0,
        description="Estimated adiabatic/flame zone temperature in Kelvin"
    )


class EAFHIResponse(BaseModel):
    """Deterministic EAFHI fire safety assessment response."""

    material_key: str
    material_name: str
    chemical_formula: str
    pressure_kpa: float
    oxygen_percentage: float
    gravity_level: str
    gravity_ms2: float

    # Gas mixture thermodynamics
    gas_density_kg_m3: float = Field(..., description="Atmospheric gas mixture density rho via ideal gas law")
    sutherland_viscosity_pa_s: float = Field(..., description="Dynamic viscosity mu via Sutherland formula")
    kinematic_viscosity_m2_s: float = Field(..., description="Kinematic viscosity nu = mu / rho")

    # Hydrodynamic convection and buoyancy metrics
    grashof_number: float = Field(..., description="Grashof number Gr = g * beta * (Tf - Tinf) * L^3 / nu^2")
    buoyancy_velocity_m_s: float = Field(..., description="Natural buoyancy buoyant velocity U_buoy = sqrt(g * beta * DeltaT * L)")
    effective_velocity_m_s: float = Field(..., description="Mixed convection effective velocity U_eff = sqrt(U_vent^2 + U_buoy^2)")
    buoyancy_factor: float = Field(..., description="Suppressed buoyancy enhancement factor Phi_buoyancy(Gr)")

    # Oxygen thresholds & margins
    limiting_oxygen_index_std: float = Field(..., description="Standard 1g sea-level Limiting Oxygen Index (LOI) %")
    moc_percentage: float = Field(..., description="Minimum Extinguishing Oxygen Concentration under hypobaric/reduced-g conditions")
    oxygen_partial_pressure_kpa: float = Field(..., description="Oxygen partial pressure P_O2 = P * X_O2")
    oxygen_margin_pct: float = Field(..., description="Oxygen margin = X_O2 - MOC (%)")

    # Deterministic Risk Score & Hazard Classification
    eafhi_score: float = Field(..., ge=0.0, le=1.0, description="Exploration Atmosphere Fire Hazard Index strictly bounded in [0.0, 1.0]")
    flammability_class: str = Field(..., description="Classification ('CLASS_1_LOW_RISK', 'CLASS_2_MODERATE_RISK', 'CLASS_3_HIGH_RISK', 'CLASS_4_CRITICAL_RISK')")
    risk_category: str = Field(..., description="Category ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')")
    is_flammable: bool = Field(..., description="Whether ambient oxygen exceeds hypobaric MOC and triggers self-sustained combustion")
    safety_advisory: str = Field(..., description="Operational advisory for Artemis Gateway flight controllers")


class EAFHISensitivityRequest(BaseModel):
    """Payload to perform environmental sensitivity sweep over pressure, oxygen, or gravity."""

    material: str = Field(default="pmma", description="Material identifier")
    parameter_to_sweep: Literal["oxygen_percentage", "pressure_kpa", "gravity_ms2"] = Field(
        default="oxygen_percentage",
        description="Atmospheric or gravitational parameter to sweep"
    )
    min_value: Optional[float] = Field(default=None, description="Minimum sweep bound (uses sensible physical default if omitted)")
    max_value: Optional[float] = Field(default=None, description="Maximum sweep bound (uses sensible physical default if omitted)")
    steps: int = Field(default=15, ge=3, le=50, description="Number of evaluation steps")
    fixed_conditions: Optional[dict[str, Any]] = Field(
        default=None,
        description="Fixed atmospheric conditions for other dimensions"
    )


class EAFHISensitivityResponse(BaseModel):
    """Sensitivity sweep analysis response."""

    material: str
    parameter_swept: str
    sweep_values: list[float]
    eafhi_scores: list[float]
    grashof_numbers: list[float]
    flammability_classes: list[str]
    critical_threshold_value: Optional[float] = Field(
        default=None,
        description="Sweep parameter value where material transitions across the flammability threshold"
    )


class GatewayProfileResponse(BaseModel):
    """Artemis Gateway comparative evaluation across all aerospace cabin materials."""

    atmosphere_name: str
    pressure_kpa: float
    oxygen_percentage: float
    gravity_level: str
    material_evaluations: list[EAFHIResponse]
    critical_risk_count: int
    high_risk_count: int
    highest_risk_material: str
    lowest_risk_material: str
    gateway_safety_summary: str
