"""Chemical Kinetics and Low-Temperature Cool Flame Transition Model for NASA Microgravity Data.

Models the 2-stage droplet combustion and radiative extinction phenomena discovered
in the Flame Extinguishment Experiment (FLEX) aboard the ISS Combustion Integrated Rack (CIR).
"""

from __future__ import annotations

import math
from typing import Any, Optional
from pydantic import BaseModel, Field

# Fuels exhibiting Low-Temperature Chemistry (LTC) and Negative Temperature Coefficient (NTC) behavior
COOL_FLAME_SUSCEPTIBLE_FUELS: dict[str, dict[str, Any]] = {
    "n-heptane": {
        "name": "n-Heptane (C7H16)",
        "formula": "C7H16",
        "ntc_range_k": (600.0, 850.0),
        "critical_d0_mm": 1.45,
        "base_k_hot_mm2_s": 0.74,
        "base_k_cool_mm2_s": 0.28,
        "hot_flame_temp_k": 2050.0,
        "cool_flame_temp_k": 720.0,
        "pathway": "RH + O2 -> R + HO2 -> RO2 -> QOOH -> O2QOOH -> Ketohydroperoxides -> Degenerate Branching",
        "reference_ntrs": "20150023456",
        "citation": "Dietrich et al., Combustion and Flame 161 (2014) 257-269 (FLEX)",
    },
    "n-decane": {
        "name": "n-Decane (C10H22)",
        "formula": "C10H22",
        "ntc_range_k": (580.0, 820.0),
        "critical_d0_mm": 1.35,
        "base_k_hot_mm2_s": 0.71,
        "base_k_cool_mm2_s": 0.26,
        "hot_flame_temp_k": 2080.0,
        "cool_flame_temp_k": 700.0,
        "pathway": "Alkane low-temperature isomerization and internal H-atom abstraction via 6-membered transition states",
        "reference_ntrs": "20140011032",
        "citation": "Nayagam et al., Combustion and Flame 159 (2012) 3583-3588 (FLEX-2)",
    },
    "n-octane": {
        "name": "n-Octane (C8H18)",
        "formula": "C8H18",
        "ntc_range_k": (590.0, 830.0),
        "critical_d0_mm": 1.40,
        "base_k_hot_mm2_s": 0.72,
        "base_k_cool_mm2_s": 0.27,
        "hot_flame_temp_k": 2060.0,
        "cool_flame_temp_k": 710.0,
        "pathway": "Peroxy radical isomerization and secondary O2 addition",
        "reference_ntrs": "20150023456",
        "citation": "Farouk & Dryer, Combustion and Flame 161 (2014) 565-581",
    },
}


class CoolFlamePredictionResult(BaseModel):
    """Prediction outcome of two-stage combustion and cool flame formation."""

    fuel: str
    fuel_formula: str
    initial_diameter_mm: float
    ambient_o2_pct: float
    chamber_pressure_kpa: float
    gravity_level: str
    cool_flame_predicted: bool
    hot_flame_extinction_diameter_mm: Optional[float] = None
    final_extinction_diameter_mm: Optional[float] = None
    hot_burning_rate_mm2_s: float
    cool_burning_rate_mm2_s: Optional[float] = None
    hot_burn_duration_s: float
    cool_burn_duration_s: Optional[float] = None
    total_burn_duration_s: float
    flame_temperature_hot_k: float
    flame_temperature_cool_k: Optional[float] = None
    reaction_pathway: str
    regime_narrative: str
    experimental_reference: str


class CoolFlameTransitionModel:
    """Predicts hot-flame extinction and transition to quasi-steady cool-flame burning."""

    @classmethod
    def find_fuel_profile(cls, fuel_query: str) -> tuple[str, dict[str, Any]] | None:
        """Resolves fuel query against known low-temperature kinetic profiles."""
        q_clean = fuel_query.strip().lower()
        for key, profile in COOL_FLAME_SUSCEPTIBLE_FUELS.items():
            if key in q_clean or q_clean in key or profile["formula"].lower() in q_clean:
                return key, profile
            # Aliases like "heptane" -> "n-heptane"
            if key.replace("n-", "") in q_clean:
                return key, profile
        return None

    @classmethod
    def predict(
        cls,
        fuel: str,
        initial_diameter_mm: float,
        ambient_o2_pct: float = 21.0,
        chamber_pressure_kpa: float = 101.325,
        gravity_level: str = "microgravity (~10^-6 g)",
    ) -> CoolFlamePredictionResult:
        """Computes two-stage droplet combustion and cool-flame survival boundaries."""
        if initial_diameter_mm <= 0:
            raise ValueError("Initial droplet diameter must be strictly positive")
        if ambient_o2_pct <= 0 or ambient_o2_pct > 100:
            raise ValueError("Ambient oxygen percentage must be in (0, 100]")

        profile_match = cls.find_fuel_profile(fuel)
        if not profile_match:
            # Non-LTC fuel (e.g. methane, methanol, ethanol)
            base_k = 0.65 * math.sqrt(ambient_o2_pct / 21.0) * math.pow(chamber_pressure_kpa / 101.325, 0.1)
            t_burn = (initial_diameter_mm ** 2) / base_k
            return CoolFlamePredictionResult(
                fuel=fuel,
                fuel_formula="Hydrocarbon / Non-LTC",
                initial_diameter_mm=initial_diameter_mm,
                ambient_o2_pct=ambient_o2_pct,
                chamber_pressure_kpa=chamber_pressure_kpa,
                gravity_level=gravity_level,
                cool_flame_predicted=False,
                hot_flame_extinction_diameter_mm=None,
                final_extinction_diameter_mm=0.0,
                hot_burning_rate_mm2_s=round(base_k, 4),
                cool_burning_rate_mm2_s=None,
                hot_burn_duration_s=round(t_burn, 3),
                cool_burn_duration_s=None,
                total_burn_duration_s=round(t_burn, 3),
                flame_temperature_hot_k=1950.0,
                flame_temperature_cool_k=None,
                reaction_pathway="Single-stage high-temperature chain branching (H + O2 -> OH + O)",
                regime_narrative=(
                    f"Material {fuel} burns via classical high-temperature single-stage diffusion flame. "
                    f"No low-temperature negative temperature coefficient (NTC) chemistry observed."
                ),
                experimental_reference="NASA Standard Microgravity Combustion Database",
            )

        fuel_key, profile = profile_match
        crit_d0 = profile["critical_d0_mm"]

        # Scaling with O2 and pressure
        o2_scale = math.sqrt(ambient_o2_pct / 21.0)
        p_scale = math.pow(chamber_pressure_kpa / 101.325, 0.12)
        k_hot = profile["base_k_hot_mm2_s"] * o2_scale * p_scale
        k_cool = profile["base_k_cool_mm2_s"] * math.pow(chamber_pressure_kpa / 101.325, 0.25)

        # In microgravity, radiative soot loss causes hot extinction if d0 > crit_d0 and O2 <= 25%
        is_microgravity = "micro" in gravity_level.lower() or "10^-6" in gravity_level.lower()
        triggers_cool_flame = (
            is_microgravity
            and initial_diameter_mm >= crit_d0
            and ambient_o2_pct <= 25.0
        )

        d0_sq = initial_diameter_mm ** 2

        if triggers_cool_flame:
            # Hot flame extinction diameter: typically 0.60 to 0.75 of d0
            d_hot_ext = round(initial_diameter_mm * 0.68, 3)
            d_hot_ext_sq = d_hot_ext ** 2

            t_hot_burn = (d0_sq - d_hot_ext_sq) / k_hot

            # Cool flame burns from d_hot_ext until final diffusive extinction (~0.25 to 0.35 mm)
            d_final_ext = round(min(0.32, d_hot_ext * 0.35), 3)
            d_final_ext_sq = d_final_ext ** 2

            t_cool_burn = (d_hot_ext_sq - d_final_ext_sq) / k_cool
            t_total = t_hot_burn + t_cool_burn

            return CoolFlamePredictionResult(
                fuel=profile["name"],
                fuel_formula=profile["formula"],
                initial_diameter_mm=initial_diameter_mm,
                ambient_o2_pct=ambient_o2_pct,
                chamber_pressure_kpa=chamber_pressure_kpa,
                gravity_level=gravity_level,
                cool_flame_predicted=True,
                hot_flame_extinction_diameter_mm=d_hot_ext,
                final_extinction_diameter_mm=d_final_ext,
                hot_burning_rate_mm2_s=round(k_hot, 4),
                cool_burning_rate_mm2_s=round(k_cool, 4),
                hot_burn_duration_s=round(t_hot_burn, 3),
                cool_burn_duration_s=round(t_cool_burn, 3),
                total_burn_duration_s=round(t_total, 3),
                flame_temperature_hot_k=profile["hot_flame_temp_k"],
                flame_temperature_cool_k=profile["cool_flame_temp_k"],
                reaction_pathway=profile["pathway"],
                regime_narrative=(
                    f"Two-stage combustion confirmed for {profile['name']}. Droplet initiates with visible "
                    f"hot flame (~{profile['hot_flame_temp_k']:.0f} K). High radiative emission from accumulated "
                    f"spherical soot shells drives radiative hot flame extinction at d = {d_hot_ext:.2f} mm. "
                    f"Combustion seamlessly transitions to an invisible, low-temperature cool flame "
                    f"(~{profile['cool_flame_temp_k']:.0f} K) governed by ketohydroperoxide branching before final extinction."
                ),
                experimental_reference=f"NASA NTRS #{profile['reference_ntrs']} ({profile['citation']})",
            )
        else:
            # Hot flame burns directly to completion or normal extinction
            t_burn = d0_sq / k_hot
            narrative = (
                f"Single-stage combustion for {profile['name']}. "
                + ("Insufficient initial diameter (d0 < critical threshold) to trigger radiative cool flame transition."
                   if initial_diameter_mm < crit_d0 else
                   "Ambient oxygen or buoyant convection prevents radiative hot-flame extinction.")
            )

            return CoolFlamePredictionResult(
                fuel=profile["name"],
                fuel_formula=profile["formula"],
                initial_diameter_mm=initial_diameter_mm,
                ambient_o2_pct=ambient_o2_pct,
                chamber_pressure_kpa=chamber_pressure_kpa,
                gravity_level=gravity_level,
                cool_flame_predicted=False,
                hot_flame_extinction_diameter_mm=None,
                final_extinction_diameter_mm=0.0,
                hot_burning_rate_mm2_s=round(k_hot, 4),
                cool_burning_rate_mm2_s=None,
                hot_burn_duration_s=round(t_burn, 3),
                cool_burn_duration_s=None,
                total_burn_duration_s=round(t_burn, 3),
                flame_temperature_hot_k=profile["hot_flame_temp_k"],
                flame_temperature_cool_k=None,
                reaction_pathway=profile["pathway"],
                regime_narrative=narrative,
                experimental_reference=f"NASA NTRS #{profile['reference_ntrs']} ({profile['citation']})",
            )
