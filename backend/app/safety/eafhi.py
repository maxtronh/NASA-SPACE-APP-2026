"""Exploration Atmosphere Fire Hazard Index (EAFHI) Engine (Upgrade E-10).

Features:
- Grashof formulation with Sutherland gas viscosity and ideal gas mixture density.
- Natural and mixed convection buoyancy enhancement factor: Phi_buoyancy(Gr) = 1 / (1 + (Gr / 10^6)^0.4).
- Hypobaric and reduced-gravity Minimum Extinguishing Oxygen Concentration (MOC).
- Deterministic, physics-grounded EAFHI risk score strictly bounded in [0.0, 1.0].
- Flammability risk classification: CLASS_1_LOW_RISK, CLASS_2_MODERATE_RISK, CLASS_3_HIGH_RISK, CLASS_4_CRITICAL_RISK.
- Multi-material Artemis Lunar Gateway flammability assessment across standard aerospace materials.
- Environmental sensitivity sweep analysis over oxygen, pressure, and gravity.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from backend.app.core.gravity import (
    GravityLevel,
    get_gravity_acceleration,
    normalize_gravity_level,
)
from backend.app.safety.standards import (
    CABIN_ATMOSPHERES,
    SPACECRAFT_MATERIALS,
    MaterialFlammabilityProfile,
)

# Reference Standard Atmospheric Constants
P_STD_KPA = 101.325
XO2_STD_PCT = 21.0
T_INF_K = 298.15  # Standard cabin ambient temperature (25 °C)
R_UNIVERSAL = 8.314462618  # J / (mol * K)

# Gas Molecular Weights (kg / mol)
M_O2 = 0.032000
M_N2 = 0.0280134

# Sutherland Viscosity Constants for Air/N2/O2 Mixtures
SUTHERLAND_MU0 = 1.716e-5  # Pa * s at T0
SUTHERLAND_T0 = 273.15     # K
SUTHERLAND_S = 110.4       # Sutherland temperature constant in K

# Weighting coefficients for EAFHI formula
W1_OXYGEN = 0.40
W2_PRESSURE = 0.25
W3_BUOYANCY = 0.25
W_MATERIAL = 0.20

# Flammability Classification Thresholds
CLASS_1_LIMIT = 0.35
CLASS_2_LIMIT = 0.65
CLASS_3_LIMIT = 0.85


class EAFHIEngine:
    """Calculates Exploration Atmosphere Fire Hazard Index for aerospace cabin environments."""

    @classmethod
    def calculate_gas_properties(
        cls,
        pressure_kpa: float,
        oxygen_percentage: float,
        ambient_temp_k: float = T_INF_K,
    ) -> tuple[float, float, float]:
        """Calculates gas mixture density (rho), Sutherland dynamic viscosity (mu), and kinematic viscosity (nu).

        Returns:
            (density_kg_m3, dynamic_viscosity_pa_s, kinematic_viscosity_m2_s)
        """
        # Mole fractions
        y_o2 = max(0.0, min(1.0, oxygen_percentage / 100.0))
        y_n2 = 1.0 - y_o2

        # Average molecular weight
        m_mix = y_o2 * M_O2 + y_n2 * M_N2

        # Ideal gas mixture density rho = (P * M) / (R_u * T)
        p_pa = pressure_kpa * 1000.0
        rho = (p_pa * m_mix) / (R_UNIVERSAL * ambient_temp_k)

        # Sutherland dynamic viscosity
        t = ambient_temp_k
        mu = SUTHERLAND_MU0 * ((t / SUTHERLAND_T0) ** 1.5) * ((SUTHERLAND_T0 + SUTHERLAND_S) / (t + SUTHERLAND_S))

        # Kinematic viscosity nu = mu / rho
        nu = mu / max(rho, 1e-6)

        return rho, mu, nu

    @classmethod
    def calculate_grashof_number(
        cls,
        gravity_ms2: float,
        characteristic_length_m: float = 0.05,
        flame_temperature_k: float = 1800.0,
        ambient_temp_k: float = T_INF_K,
        kinematic_viscosity_m2_s: float = 2.76e-5,
    ) -> float:
        """Calculates Grashof number: Gr = g * beta * (T_f - T_inf) * L^3 / nu^2."""
        beta = 1.0 / ambient_temp_k
        delta_t = max(0.0, flame_temperature_k - ambient_temp_k)
        l_cubed = characteristic_length_m ** 3
        nu_squared = kinematic_viscosity_m2_s ** 2

        g = max(0.0, gravity_ms2)
        gr = (g * beta * delta_t * l_cubed) / max(nu_squared, 1e-18)
        return float(gr)

    @classmethod
    def calculate_buoyancy_factor(cls, grashof_number: float) -> float:
        """Buoyancy enhancement factor: Phi_buoyancy(Gr) = 1 / (1 + (Gr / 10^6)^0.4)."""
        gr_safe = max(0.0, grashof_number)
        phi = 1.0 / (1.0 + (gr_safe / 1e6) ** 0.4)
        return float(phi)

    @classmethod
    def calculate_hypobaric_moc(
        cls,
        limiting_oxygen_index_std: float,
        pressure_kpa: float,
        gravity_ms2: float,
    ) -> float:
        """Calculates hypobaric and reduced-gravity Minimum Extinguishing Oxygen Concentration (MOC).

        Formulation:
        MOC(P, g) = LOI_std * (P / P_std)^(-0.22) * (1.0 - 0.08 * ln(max(g, 1e-5) + 1.0))
        """
        p_ratio = max(0.01, pressure_kpa / P_STD_KPA)
        g_safe = max(1e-5, gravity_ms2)

        moc = (
            limiting_oxygen_index_std
            * (p_ratio ** (-0.22))
            * (1.0 - 0.08 * math.log(g_safe + 1.0))
        )
        return float(max(1.0, moc))

    @classmethod
    def resolve_material(cls, material_key_or_name: str) -> tuple[str, MaterialFlammabilityProfile]:
        """Resolves material key or common name to standard profile."""
        clean = material_key_or_name.strip().lower()
        if clean in SPACECRAFT_MATERIALS:
            return clean, SPACECRAFT_MATERIALS[clean]

        for k, prof in SPACECRAFT_MATERIALS.items():
            if clean in prof.name.lower() or k in clean:
                return k, prof

        # Default fallback to PMMA if unrecognized
        return "pmma", SPACECRAFT_MATERIALS["pmma"]

    @classmethod
    def calculate_eafhi(
        cls,
        material: str = "pmma",
        pressure_kpa: float = 56.5,
        oxygen_percentage: float = 34.0,
        gravity_level: str = "lunar_gravity (0.16 g)",
        characteristic_length_m: float = 0.05,
        ventilation_velocity_cm_s: float = 3.0,
        flame_temperature_k: float = 1800.0,
    ) -> dict[str, Any]:
        """Calculates deterministic EAFHI score and comprehensive fire safety hazard parameters."""
        mat_key, mat_profile = cls.resolve_material(material)

        # Gravitational acceleration
        gravity_ms2 = get_gravity_acceleration(gravity_level)

        # Gas thermodynamics
        rho, mu, nu = cls.calculate_gas_properties(pressure_kpa, oxygen_percentage, T_INF_K)

        # Grashof number & buoyancy factor
        gr = cls.calculate_grashof_number(
            gravity_ms2=gravity_ms2,
            characteristic_length_m=characteristic_length_m,
            flame_temperature_k=flame_temperature_k,
            ambient_temp_k=T_INF_K,
            kinematic_viscosity_m2_s=nu,
        )
        phi_buoy = cls.calculate_buoyancy_factor(gr)

        # Convective velocities
        beta = 1.0 / T_INF_K
        delta_t = max(0.0, flame_temperature_k - T_INF_K)
        u_buoy = math.sqrt(max(0.0, gravity_ms2 * beta * delta_t * characteristic_length_m))
        u_vent = ventilation_velocity_cm_s / 100.0  # m/s
        u_eff = math.sqrt(u_vent ** 2 + u_buoy ** 2)

        # MOC and partial pressure
        loi_std = mat_profile.limiting_oxygen_index
        moc = cls.calculate_hypobaric_moc(loi_std, pressure_kpa, gravity_ms2)
        p_o2 = pressure_kpa * (oxygen_percentage / 100.0)
        oxygen_margin = oxygen_percentage - moc
        is_flammable = oxygen_percentage >= moc

        # Deterministic EAFHI Score bounded in [0.0, 1.0]:
        # EAFHI = clip(w1 * (X_O2 / X_O2_std) + w2 * (P / P_std)^(-0.5) + w3 * Phi_buoyancy(Gr) + Delta_mat, 0.0, 1.0)
        # where Delta_mat = 0.20 * (21.0 - LOI) / 21.0
        delta_mat = W_MATERIAL * ((XO2_STD_PCT - loi_std) / XO2_STD_PCT)
        raw_score = (
            W1_OXYGEN * (oxygen_percentage / XO2_STD_PCT)
            + W2_PRESSURE * ((pressure_kpa / P_STD_KPA) ** (-0.5))
            + W3_BUOYANCY * phi_buoy
            + delta_mat
        )
        eafhi_score = max(0.0, min(1.0, float(raw_score)))

        # Flammability Classification
        if eafhi_score < CLASS_1_LIMIT:
            flammability_class = "CLASS_1_LOW_RISK"
            risk_category = "LOW"
        elif eafhi_score < CLASS_2_LIMIT:
            flammability_class = "CLASS_2_MODERATE_RISK"
            risk_category = "MODERATE"
        elif eafhi_score < CLASS_3_LIMIT:
            flammability_class = "CLASS_3_HIGH_RISK"
            risk_category = "HIGH"
        else:
            flammability_class = "CLASS_4_CRITICAL_RISK"
            risk_category = "CRITICAL"

        # Advisory generation
        if flammability_class == "CLASS_4_CRITICAL_RISK":
            advisory = (
                f"CRITICAL FIRE HAZARD: {mat_profile.name} exhibits EAFHI score {eafhi_score:.3f} under "
                f"hypobaric {pressure_kpa:.1f} kPa / {oxygen_percentage:.1f}% O2 conditions. "
                f"Oxygen concentration exceeds hypobaric MOC ({moc:.1f}%) by {oxygen_margin:.1f}%. "
                f"Unrestricted ignition and self-propagating flame spread will occur. Material must be restricted "
                f"or enclosed within fire-barrier modules."
            )
        elif flammability_class == "CLASS_3_HIGH_RISK":
            advisory = (
                f"HIGH FIRE RISK: {mat_profile.name} exhibits elevated flammability (EAFHI {eafhi_score:.3f}). "
                f"Suppressed buoyancy factor ({phi_buoy:.3f}) and elevated oxygen ({oxygen_percentage:.1f}%) "
                f"substantially reduce extinction resistance. Flammability margin is {oxygen_margin:.1f}%. "
                f"Enforce secondary thermal containment."
            )
        elif flammability_class == "CLASS_2_MODERATE_RISK":
            advisory = (
                f"MODERATE RISK: {mat_profile.name} is marginally compliant (EAFHI {eafhi_score:.3f}). "
                f"Local forced ventilation current ({ventilation_velocity_cm_s:.1f} cm/s) controls flame attachment. "
                f"Maintain active airflow monitoring."
            )
        else:
            advisory = (
                f"LOW RISK (INHERENTLY SAFE): {mat_profile.name} exhibits low flammability (EAFHI {eafhi_score:.3f}). "
                f"Material LOI ({loi_std:.1f}%) significantly exceeds ambient oxygen ({oxygen_percentage:.1f}%). "
                f"Safe for open cabin installation."
            )

        return {
            "material_key": mat_key,
            "material_name": mat_profile.name,
            "chemical_formula": mat_profile.chemical_formula,
            "pressure_kpa": round(pressure_kpa, 2),
            "oxygen_percentage": round(oxygen_percentage, 2),
            "gravity_level": normalize_gravity_level(gravity_level),
            "gravity_ms2": round(gravity_ms2, 5),
            "gas_density_kg_m3": round(rho, 4),
            "sutherland_viscosity_pa_s": float(f"{mu:.6e}"),
            "kinematic_viscosity_m2_s": float(f"{nu:.6e}"),
            "grashof_number": round(gr, 2),
            "buoyancy_velocity_m_s": round(u_buoy, 4),
            "effective_velocity_m_s": round(u_eff, 4),
            "buoyancy_factor": round(phi_buoy, 4),
            "limiting_oxygen_index_std": round(loi_std, 1),
            "moc_percentage": round(moc, 2),
            "oxygen_partial_pressure_kpa": round(p_o2, 3),
            "oxygen_margin_pct": round(oxygen_margin, 2),
            "eafhi_score": round(eafhi_score, 4),
            "flammability_class": flammability_class,
            "risk_category": risk_category,
            "is_flammable": is_flammable,
            "safety_advisory": advisory,
        }

    @classmethod
    def evaluate_gateway_profile(cls) -> dict[str, Any]:
        """Evaluates all 6 standard aerospace materials under Artemis Lunar Gateway specifications.

        Gateway conditions:
        P = 56.5 kPa, X_O2 = 34.0%, g = 0.166 g (1.6279 m/s^2), V_vent = 3.0 cm/s
        """
        gateway_p = CABIN_ATMOSPHERES["artemis_gateway"].pressure_kpa
        gateway_o2 = CABIN_ATMOSPHERES["artemis_gateway"].oxygen_percentage
        gateway_g = GravityLevel.LUNAR.value

        evaluations: list[dict[str, Any]] = []
        critical_count = 0
        high_count = 0

        for key in SPACECRAFT_MATERIALS.keys():
            res = cls.calculate_eafhi(
                material=key,
                pressure_kpa=gateway_p,
                oxygen_percentage=gateway_o2,
                gravity_level=gateway_g,
                characteristic_length_m=0.05,
                ventilation_velocity_cm_s=3.0,
            )
            evaluations.append(res)
            if res["flammability_class"] == "CLASS_4_CRITICAL_RISK":
                critical_count += 1
            elif res["flammability_class"] == "CLASS_3_HIGH_RISK":
                high_count += 1

        # Sort evaluations by EAFHI score descending
        evaluations.sort(key=lambda x: x["eafhi_score"], reverse=True)

        highest = evaluations[0]["material_name"]
        lowest = evaluations[-1]["material_name"]

        summary = (
            f"Artemis Lunar Gateway Evaluation (56.5 kPa, 34.0% O2, 0.166 g): "
            f"{critical_count} critical-risk materials ({highest} highest hazard at EAFHI {evaluations[0]['eafhi_score']:.3f}), "
            f"{high_count} high-risk materials, and {len(evaluations) - critical_count - high_count} compliant materials "
            f"({lowest} safest at EAFHI {evaluations[-1]['eafhi_score']:.3f})."
        )

        return {
            "atmosphere_name": "Artemis Lunar Gateway Exploration Atmosphere",
            "pressure_kpa": gateway_p,
            "oxygen_percentage": gateway_o2,
            "gravity_level": gateway_g,
            "material_evaluations": evaluations,
            "critical_risk_count": critical_count,
            "high_risk_count": high_count,
            "highest_risk_material": highest,
            "lowest_risk_material": lowest,
            "gateway_safety_summary": summary,
        }

    @classmethod
    def sensitivity_sweep(
        cls,
        material: str = "pmma",
        parameter_to_sweep: str = "oxygen_percentage",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        steps: int = 15,
        fixed_conditions: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Performs parametric sweep across oxygen_percentage, pressure_kpa, or gravity_ms2."""
        mat_key, _ = cls.resolve_material(material)
        fixed = fixed_conditions or {}

        base_p = float(fixed.get("pressure_kpa", 56.5))
        base_o2 = float(fixed.get("oxygen_percentage", 34.0))
        base_g_ms2 = float(fixed.get("gravity_ms2", 1.62))
        base_l = float(fixed.get("characteristic_length_m", 0.05))
        base_v = float(fixed.get("ventilation_velocity_cm_s", 3.0))

        # Determine sweep bounds
        param = parameter_to_sweep.strip().lower()
        if param == "oxygen_percentage":
            low = min_value if min_value is not None else 15.0
            high = max_value if max_value is not None else 50.0
        elif param == "pressure_kpa":
            low = min_value if min_value is not None else 30.0
            high = max_value if max_value is not None else 120.0
        elif param in ("gravity_ms2", "gravity"):
            low = min_value if min_value is not None else 1e-4
            high = max_value if max_value is not None else 15.0
        else:
            raise ValueError(f"Unsupported parameter_to_sweep: {parameter_to_sweep}")

        num_steps = max(3, min(50, steps))
        sweep_values = [low + i * (high - low) / (num_steps - 1) for i in range(num_steps)]

        scores: list[float] = []
        grashofs: list[float] = []
        classes: list[str] = []
        critical_threshold: Optional[float] = None

        prev_flammable: Optional[bool] = None

        for val in sweep_values:
            cur_p = val if param == "pressure_kpa" else base_p
            cur_o2 = val if param == "oxygen_percentage" else base_o2
            cur_g = val if param in ("gravity_ms2", "gravity") else base_g_ms2

            res = cls.calculate_eafhi(
                material=mat_key,
                pressure_kpa=cur_p,
                oxygen_percentage=cur_o2,
                gravity_level=f"{cur_g} m/s^2",
                characteristic_length_m=base_l,
                ventilation_velocity_cm_s=base_v,
            )

            scores.append(res["eafhi_score"])
            grashofs.append(res["grashof_number"])
            classes.append(res["flammability_class"])

            # Detect flammability transition threshold
            is_flam = res["is_flammable"]
            if prev_flammable is not None and is_flam != prev_flammable and critical_threshold is None:
                critical_threshold = round(val, 2)
            prev_flammable = is_flam

        return {
            "material": mat_key,
            "parameter_swept": param,
            "sweep_values": [round(v, 3) for v in sweep_values],
            "eafhi_scores": scores,
            "grashof_numbers": grashofs,
            "flammability_classes": classes,
            "critical_threshold_value": critical_threshold,
        }
