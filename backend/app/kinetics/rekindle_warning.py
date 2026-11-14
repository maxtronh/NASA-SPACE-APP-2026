"""Low-Temperature Chemistry (LTC) and Silent Cool-Flame Rekindling Early Warning Engine (Upgrade E-11).

Formulates the cool-flame Damköhler number (Da_cool) and probabilistic rekindling hazard
for alkane droplet combustion observed in NASA CIR FLEX experiments.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from backend.app.schemas.rekindle import (
    CoolFlameStreamMonitorRequest,
    CoolFlameStreamMonitorResponse,
    ExtinctionAssessment,
    LTCParameters,
    RekindleWarningRequest,
    RekindleWarningResponse,
)

# Universal gas constant in J / (mol * K)
R_GAS_CONSTANT: float = 8.314462618

# Minimum numerical clamp bounds
MIN_VELOCITY_FLOOR: float = 1e-4  # m/s, physical diffusive limit
SIGMOID_CLAMP_MAX: float = 100.0
SIGMOID_CLAMP_MIN: float = -100.0

# Authoritative LTC Kinetic Parameters for Spacecraft Fire Safety
LTC_FUEL_PROFILES: dict[str, dict[str, Any]] = {
    "n-heptane": {
        "name": "n-Heptane",
        "formula": "C7H16",
        "supports_ltc": True,
        "flash_point_k": 269.15,      # -4.0 °C
        "boiling_point_k": 371.55,    # 98.4 °C
        "e_ltc_j_mol": 68000.0,       # 68.0 kJ/mol
        "a_ltc_s_inv": 1.50e6,        # s^-1
        "da_crit": 1.0,
        "theta": 0.20,
        "ntc_range_k": (600.0, 850.0),
        "typical_cool_temp_k": 720.0,
    },
    "n-octane": {
        "name": "n-Octane",
        "formula": "C8H18",
        "supports_ltc": True,
        "flash_point_k": 286.15,      # 13.0 °C
        "boiling_point_k": 398.75,    # 125.6 °C
        "e_ltc_j_mol": 72000.0,       # 72.0 kJ/mol
        "a_ltc_s_inv": 1.80e6,        # s^-1
        "da_crit": 1.0,
        "theta": 0.20,
        "ntc_range_k": (590.0, 830.0),
        "typical_cool_temp_k": 710.0,
    },
    "n-decane": {
        "name": "n-Decane",
        "formula": "C10H22",
        "supports_ltc": True,
        "flash_point_k": 319.15,      # 46.0 °C
        "boiling_point_k": 447.25,    # 174.1 °C
        "e_ltc_j_mol": 78000.0,       # 78.0 kJ/mol
        "a_ltc_s_inv": 2.20e6,        # s^-1
        "da_crit": 1.0,
        "theta": 0.20,
        "ntc_range_k": (580.0, 820.0),
        "typical_cool_temp_k": 700.0,
    },
    "methanol": {
        "name": "Methanol",
        "formula": "CH3OH",
        "supports_ltc": False,
        "flash_point_k": 284.15,      # 11.0 °C
        "boiling_point_k": 337.85,
        "e_ltc_j_mol": None,
        "a_ltc_s_inv": None,
        "da_crit": 1.0,
        "theta": 0.20,
        "ntc_range_k": None,
        "typical_cool_temp_k": None,
    },
    "ethanol": {
        "name": "Ethanol",
        "formula": "C2H5OH",
        "supports_ltc": False,
        "flash_point_k": 286.15,      # 13.0 °C
        "boiling_point_k": 351.52,
        "e_ltc_j_mol": None,
        "a_ltc_s_inv": None,
        "da_crit": 1.0,
        "theta": 0.20,
        "ntc_range_k": None,
        "typical_cool_temp_k": None,
    },
    "methane": {
        "name": "Methane",
        "formula": "CH4",
        "supports_ltc": False,
        "flash_point_k": 90.65,       # Cryogenic
        "boiling_point_k": 111.65,
        "e_ltc_j_mol": None,
        "a_ltc_s_inv": None,
        "da_crit": 1.0,
        "theta": 0.20,
        "ntc_range_k": None,
        "typical_cool_temp_k": None,
    },
}

# Alias map for tolerant lookup
FUEL_ALIASES: dict[str, str] = {
    "heptane": "n-heptane",
    "c7h16": "n-heptane",
    "octane": "n-octane",
    "c8h18": "n-octane",
    "decane": "n-decane",
    "c10h22": "n-decane",
    "ch3oh": "methanol",
    "methyl alcohol": "methanol",
    "c2h5oh": "ethanol",
    "ethyl alcohol": "ethanol",
    "ch4": "methane",
}


class RekindleWarningEngine:
    """Low-temperature kinetics and cool-flame rekindling hazard assessment engine."""

    @classmethod
    def resolve_fuel_profile(cls, fuel_name: str) -> tuple[str, dict[str, Any]]:
        """Resolves fuel profile case-insensitively, supporting standard names and aliases."""
        clean_name = fuel_name.strip().lower()
        canonical_key = FUEL_ALIASES.get(clean_name, clean_name)
        if canonical_key in LTC_FUEL_PROFILES:
            return canonical_key, LTC_FUEL_PROFILES[canonical_key]

        supported = list(LTC_FUEL_PROFILES.keys())
        raise ValueError(
            f"Unsupported fuel '{fuel_name}'. Available fuels in LTC database: {supported}"
        )

    @classmethod
    def calculate_damkohler_cool(
        cls,
        characteristic_length_m: float,
        ventilation_velocity_m_s: float,
        fuel: str,
        temperature_k: float,
    ) -> tuple[float, float, float | None]:
        """Calculates cool-flame Damköhler number Da_cool = tau_res / tau_chem.

        Returns:
            Tuple of (da_cool, tau_res_s, tau_chem_s)
        """
        if temperature_k <= 0.0:
            raise ValueError(f"Temperature must be strictly positive (got {temperature_k} K).")
        if characteristic_length_m <= 0.0:
            raise ValueError(f"Characteristic length must be strictly positive (got {characteristic_length_m} m).")
        if ventilation_velocity_m_s <= 0.0:
            raise ValueError(f"Ventilation velocity must be strictly positive (got {ventilation_velocity_m_s} m/s).")

        _, profile = cls.resolve_fuel_profile(fuel)

        # Flow residence time
        effective_u = max(ventilation_velocity_m_s, MIN_VELOCITY_FLOOR)
        tau_res = characteristic_length_m / effective_u

        if not profile.get("supports_ltc", False):
            return 0.0, tau_res, None

        a_ltc = profile["a_ltc_s_inv"]
        e_ltc = profile["e_ltc_j_mol"]

        if a_ltc is None or e_ltc is None:
            return 0.0, tau_res, None

        # Arrhenius rate: k_LTC = A * exp(-E / RT)
        exp_arg = -e_ltc / (R_GAS_CONSTANT * temperature_k)
        if exp_arg < -700.0:
            k_ltc = 0.0
        else:
            k_ltc = a_ltc * math.exp(exp_arg)

        if k_ltc <= 0.0:
            tau_chem = float("inf")
            da_cool = 0.0
        else:
            tau_chem = 1.0 / k_ltc
            da_cool = tau_res / tau_chem

        return da_cool, tau_res, tau_chem

    @classmethod
    def calculate_rekindle_probability(
        cls,
        damkohler_cool: float,
        fuel_temp_k: float,
        flash_point_k: float,
        da_crit: float = 1.0,
        theta: float = 0.20,
        supports_ltc: bool = True,
    ) -> float:
        """Calculates logistic rekindling probability with flash point cutoff:

        P_rekindle = [1 + exp(-(Da_cool - Da_crit) / theta)]^(-1) * I(T_fuel > T_flash)
        """
        if not supports_ltc:
            return 0.0

        # Strict physical indicator: below flash point, vapor pressure is below LFL
        if fuel_temp_k <= flash_point_k:
            return 0.0

        if theta <= 0.0:
            raise ValueError(f"Transition scale theta must be strictly positive (got {theta}).")

        exponent = -(damkohler_cool - da_crit) / theta

        # Prevent overflow in math.exp
        if exponent > SIGMOID_CLAMP_MAX:
            return 0.0
        elif exponent < SIGMOID_CLAMP_MIN:
            return 1.0

        p = 1.0 / (1.0 + math.exp(exponent))
        return min(max(p, 0.0), 1.0)

    @classmethod
    def classify_risk(cls, rekindle_prob: float) -> str:
        """Classifies rekindling hazard according to NASA Spaceflight Hazard severity envelope."""
        if rekindle_prob < 0.20:
            return "INERT"
        elif rekindle_prob < 0.70:
            return "MONITOR"
        elif rekindle_prob < 0.85:
            return "REKINDLE_WARNING"
        else:
            return "CRITICAL_REKINDLE_HAZARD"

    @classmethod
    def calculate_critical_ventilation(
        cls,
        characteristic_length_m: float,
        fuel: str,
        temperature_k: float,
        da_crit: float = 1.0,
    ) -> float:
        """Calculates critical ventilation velocity U_vent,crit = (L * k_LTC) / Da_crit."""
        if characteristic_length_m <= 0.0:
            raise ValueError("Characteristic length must be strictly positive.")
        if temperature_k <= 0.0:
            raise ValueError("Temperature must be strictly positive.")
        if da_crit <= 0.0:
            raise ValueError("Critical Damköhler must be strictly positive.")

        _, profile = cls.resolve_fuel_profile(fuel)
        if not profile.get("supports_ltc", False):
            return 0.0

        a_ltc = profile["a_ltc_s_inv"]
        e_ltc = profile["e_ltc_j_mol"]
        if a_ltc is None or e_ltc is None:
            return 0.0

        exp_arg = -e_ltc / (R_GAS_CONSTANT * temperature_k)
        if exp_arg < -700.0:
            k_ltc = 0.0
        else:
            k_ltc = a_ltc * math.exp(exp_arg)

        return (characteristic_length_m * k_ltc) / da_crit

    @classmethod
    def generate_advisory_message(
        cls,
        risk: str,
        da_cool: float,
        da_crit: float,
        rekindle_prob: float,
        fuel_name: str,
        temp_k: float,
        flash_point_k: float,
        u_crit_m_s: float,
        supports_ltc: bool,
    ) -> str:
        """Generates clear, operationally actionable mission control advisory."""
        if not supports_ltc:
            return (
                f"INERT: Fuel '{fuel_name}' does not possess an alkylperoxy low-temperature "
                "isomerization pathway. Silent cool-flame rekindling is physically precluded."
            )

        if temp_k <= flash_point_k:
            return (
                f"INERT: Droplet/surface temperature ({temp_k:.1f} K) is at or below the fuel closed-cup "
                f"flash point ({flash_point_k:.1f} K). Equilibrium vapor pressure cannot sustain a combustible mixture."
            )

        if risk == "CRITICAL_REKINDLE_HAZARD":
            return (
                f"CRITICAL REKINDLE HAZARD: Damköhler Da_cool ({da_cool:.2f}) >> Da_crit ({da_crit:.2f}) "
                f"with P_rekindle={rekindle_prob * 100.0:.1f}%. High-temperature reignition is imminent. "
                f"Initiate cabin air purge or increase forced ventilation above {u_crit_m_s:.3f} m/s."
            )
        elif risk == "REKINDLE_WARNING":
            return (
                f"REKINDLE WARNING: Da_cool ({da_cool:.2f}) approaching critical threshold (P_rekindle={rekindle_prob * 100.0:.1f}%). "
                f"Sub-visible cool flame active. Maintain ventilation airspeed above {u_crit_m_s:.3f} m/s to prevent radical accumulation."
            )
        elif risk == "MONITOR":
            return (
                f"MONITOR ADVISORY: Active cool-flame peroxy radicals detected at {temp_k:.1f} K (Da_cool={da_cool:.2f}, "
                f"P_rekindle={rekindle_prob * 100.0:.1f}%). Continuous thermal/radiometric observation required."
            )
        else:
            return (
                f"INERT: Da_cool ({da_cool:.3f}) is safely below critical bifurcation. "
                "Convective transport rate dominates chemical reaction timescale."
            )

    @classmethod
    def evaluate_rekindle_risk(cls, req: RekindleWarningRequest) -> RekindleWarningResponse:
        """Processes a single-state RekindleWarningRequest into a RekindleWarningResponse."""
        key, profile = cls.resolve_fuel_profile(req.fuel)

        da_cool, tau_res, tau_chem = cls.calculate_damkohler_cool(
            characteristic_length_m=req.characteristic_length_m,
            ventilation_velocity_m_s=req.ventilation_velocity_m_s,
            fuel=key,
            temperature_k=req.fuel_temperature_k,
        )

        supports_ltc = profile.get("supports_ltc", False)
        flash_k = profile["flash_point_k"]
        da_crit = profile.get("da_crit", 1.0)
        theta = profile.get("theta", 0.20)

        p_rekindle = cls.calculate_rekindle_probability(
            damkohler_cool=da_cool,
            fuel_temp_k=req.fuel_temperature_k,
            flash_point_k=flash_k,
            da_crit=da_crit,
            theta=theta,
            supports_ltc=supports_ltc,
        )

        risk = cls.classify_risk(p_rekindle)

        u_crit = cls.calculate_critical_ventilation(
            characteristic_length_m=req.characteristic_length_m,
            fuel=key,
            temperature_k=req.fuel_temperature_k,
            da_crit=da_crit,
        )

        advisory = cls.generate_advisory_message(
            risk=risk,
            da_cool=da_cool,
            da_crit=da_crit,
            rekindle_prob=p_rekindle,
            fuel_name=profile["name"],
            temp_k=req.fuel_temperature_k,
            flash_point_k=flash_k,
            u_crit_m_s=u_crit,
            supports_ltc=supports_ltc,
        )

        ltc_params = LTCParameters(
            fuel=profile["name"],
            chemical_formula=profile["formula"],
            supports_ltc=supports_ltc,
            flash_point_k=flash_k,
            activation_energy_j_mol=profile.get("e_ltc_j_mol"),
            pre_exponential_s_inv=profile.get("a_ltc_s_inv"),
            critical_damkohler=da_crit,
            transition_theta=theta,
            ntc_temperature_range_k=profile.get("ntc_range_k"),
        )

        return RekindleWarningResponse(
            test_run_id=req.test_run_id,
            fuel=profile["name"],
            fuel_formula=profile["formula"],
            supports_ltc=supports_ltc,
            fuel_temperature_k=req.fuel_temperature_k,
            flash_point_k=flash_k,
            above_flash_point=req.fuel_temperature_k > flash_k,
            ventilation_velocity_m_s=req.ventilation_velocity_m_s,
            characteristic_length_m=req.characteristic_length_m,
            residence_time_s=tau_res,
            chemical_timescale_s=tau_chem,
            damkohler_cool=da_cool,
            damkohler_crit=da_crit,
            rekindle_probability=p_rekindle,
            risk_classification=risk,
            critical_ventilation_velocity_m_s=u_crit,
            ltc_parameters=ltc_params,
            advisory_message=advisory,
        )

    @classmethod
    def analyze_stream(cls, req: CoolFlameStreamMonitorRequest) -> CoolFlameStreamMonitorResponse:
        """Analyzes a flight telemetry stream for hot flame radiative extinction and silent cool flame rekindling."""
        key, profile = cls.resolve_fuel_profile(req.fuel)
        supports_ltc = profile.get("supports_ltc", False)
        flash_k = profile["flash_point_k"]
        da_crit = profile.get("da_crit", 1.0)
        theta = profile.get("theta", 0.20)
        ntc_range = profile.get("ntc_range_k", (600.0, 850.0))

        n_pts = len(req.timestamps)
        assessments: list[ExtinctionAssessment] = []

        hot_extinction_detected = False
        hot_extinction_ts: float | None = None
        cool_flame_currently_active = False

        peak_prob = 0.0
        peak_risk = "INERT"

        # Risk severity ranking for tracking peak
        risk_ranks = {
            "INERT": 0,
            "MONITOR": 1,
            "REKINDLE_WARNING": 2,
            "CRITICAL_REKINDLE_HAZARD": 3,
        }

        # Step through time series
        for i in range(n_pts):
            t = req.timestamps[i]
            temp = req.temperatures_k[i]
            rad = req.radiometer_mw[i] if req.radiometer_mw is not None else None

            # Calculate Da and rekindle prob for point
            da_cool, _, _ = cls.calculate_damkohler_cool(
                characteristic_length_m=req.characteristic_length_m,
                ventilation_velocity_m_s=req.ventilation_velocity_m_s,
                fuel=key,
                temperature_k=temp,
            )

            prob = cls.calculate_rekindle_probability(
                damkohler_cool=da_cool,
                fuel_temp_k=temp,
                flash_point_k=flash_k,
                da_crit=da_crit,
                theta=theta,
                supports_ltc=supports_ltc,
            )

            risk = cls.classify_risk(prob)

            if prob > peak_prob:
                peak_prob = prob
            if risk_ranks.get(risk, 0) > risk_ranks.get(peak_risk, 0):
                peak_risk = risk

            # Detection of hot flame extinction:
            # 1. Temperature drops from >1000 K or sharp cooling rate dT/dt < -200 K/s into cool-flame regime
            # 2. Or radiometer drops from >2.0 mW to <= 2.0 mW while temperature remains above 550 K
            is_in_cool_window = (
                supports_ltc
                and ntc_range is not None
                and (ntc_range[0] - 50.0 <= temp <= ntc_range[1] + 50.0)
            )

            if not hot_extinction_detected:
                if i > 0:
                    dt = t - req.timestamps[i - 1]
                    dtemp = temp - req.temperatures_k[i - 1]
                    cooling_rate = dtemp / dt if dt > 0 else 0.0

                    prior_hot = req.temperatures_k[i - 1] >= 950.0
                    now_cooled = temp < 950.0

                    rad_dropped = False
                    if req.radiometer_mw is not None:
                        prior_rad = req.radiometer_mw[i - 1]
                        if prior_rad is not None and rad is not None and prior_rad > 2.0 and rad <= 2.0:
                            rad_dropped = True

                    if (prior_hot and now_cooled) or rad_dropped or (cooling_rate < -200.0 and temp < 950.0):
                        hot_extinction_detected = True
                        hot_extinction_ts = t
                else:
                    # If stream begins already in cool flame window with low radiometer
                    if is_in_cool_window:
                        if rad is None or rad <= 2.0:
                            hot_extinction_detected = True
                            hot_extinction_ts = t

            # Cool flame is active if fuel supports LTC, hot flame is extinguished (or temperature is in cool range),
            # droplet is above flash point, and radiometer indicates dark/low emission
            rad_is_dark = (rad is None or rad <= 2.0)
            is_cool_active = (
                supports_ltc
                and is_in_cool_window
                and temp > flash_k
                and rad_is_dark
                and (hot_extinction_detected or temp < 900.0)
            )

            assessments.append(
                ExtinctionAssessment(
                    timestamp_s=t,
                    temperature_k=temp,
                    radiometer_mw=rad,
                    damkohler_cool=da_cool,
                    rekindle_probability=prob,
                    risk_classification=risk,
                    cool_flame_active=is_cool_active,
                )
            )

        current_prob = assessments[-1].rekindle_probability if assessments else 0.0
        current_risk = assessments[-1].risk_classification if assessments else "INERT"
        cool_flame_currently_active = assessments[-1].cool_flame_active if assessments else False

        last_temp = req.temperatures_k[-1]
        u_crit_current = cls.calculate_critical_ventilation(
            characteristic_length_m=req.characteristic_length_m,
            fuel=key,
            temperature_k=last_temp,
            da_crit=da_crit,
        )

        # Operational status summary
        if peak_risk == "CRITICAL_REKINDLE_HAZARD" or current_risk == "CRITICAL_REKINDLE_HAZARD":
            status = "CRITICAL_ALERT: Imminent rekindling hazard. Emergency inert gas purge or high ventilation recommended."
        elif peak_risk == "REKINDLE_WARNING" or current_risk == "REKINDLE_WARNING":
            status = f"WARNING: Active cool-flame peroxy accumulation. Maintain airflow above {u_crit_current:.3f} m/s."
        elif cool_flame_currently_active or peak_risk == "MONITOR":
            status = "MONITOR: Silent cool-flame persistence observed. Temperature within NTC zone."
        else:
            status = "NOMINAL: No silent rekindling hazard detected. Droplet in extinguished/inert state."

        return CoolFlameStreamMonitorResponse(
            test_run_id=req.test_run_id,
            fuel=profile["name"],
            hot_flame_extinction_detected=hot_extinction_detected,
            hot_flame_extinction_timestamp_s=hot_extinction_ts,
            cool_flame_active=cool_flame_currently_active,
            current_rekindle_probability=current_prob,
            peak_rekindle_probability=peak_prob,
            current_risk_classification=current_risk,
            peak_risk_classification=peak_risk,
            critical_ventilation_velocity_m_s=u_crit_current,
            timeline_assessments=assessments,
            safety_status=status,
        )
