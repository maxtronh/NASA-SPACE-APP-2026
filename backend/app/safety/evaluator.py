"""NASA-STD-6001B Flammability Compliance and Spacecraft Fire Safety Evaluator."""

from __future__ import annotations

import math
from typing import Any

from backend.app.core.gravity import normalize_gravity_level
from backend.app.safety.standards import CABIN_ATMOSPHERES, SPACECRAFT_MATERIALS


class FlammabilityEvaluator:
    """Evaluates spacecraft materials flammability against NASA-STD-6001B Test 1 and Test 7."""

    TEST_1_BURN_LENGTH_LIMIT_CM = 15.24  # 6.0 inches
    TEST_7_PEAK_HRR_LIMIT_KW_M2 = 100.0  # kW/m²

    @classmethod
    def evaluate(
        cls,
        material_key: str,
        oxygen_percentage: float = 21.0,
        pressure_kpa: float = 101.325,
        thickness_mm: float = 2.0,
        gravity_level: str = "microgravity (~10^-6 g)",
        ventilation_velocity_cm_s: float = 3.0,
    ) -> dict[str, Any]:
        """Evaluates material sample against NASA-STD-6001B criteria."""
        mat_clean = material_key.strip().lower()
        profile = SPACECRAFT_MATERIALS.get(mat_clean)
        if not profile:
            # Fuzzy match
            for k, p in SPACECRAFT_MATERIALS.items():
                if k in mat_clean or mat_clean in k or mat_clean in p.name.lower():
                    profile = p
                    mat_clean = k
                    break

        if not profile:
            raise ValueError(
                f"Unknown material '{material_key}'. Supported materials: {list(SPACECRAFT_MATERIALS.keys())}"
            )

        if oxygen_percentage <= 0 or oxygen_percentage > 100:
            raise ValueError(f"Invalid oxygen percentage {oxygen_percentage}%. Must be in (0, 100].")

        if pressure_kpa <= 0 or pressure_kpa > 250:
            raise ValueError(f"Invalid pressure {pressure_kpa} kPa.")

        if thickness_mm <= 0:
            raise ValueError(f"Sample thickness must be positive, got {thickness_mm} mm.")

        loi = profile.limiting_oxygen_index
        o2_delta = oxygen_percentage - loi

        # Pressure scaling factor (p / 101.3)^0.3
        p_factor = math.pow(pressure_kpa / 101.325, 0.3)
        # Thickness inertia factor (2.0 / t)^0.5
        t_factor = math.pow(2.0 / max(thickness_mm, 0.2), 0.5)

        # Gravitational convection effect
        canonical_g = normalize_gravity_level(gravity_level)
        if "micro" in canonical_g:
            # Microgravity quiescent is self-extinguishing for many materials, but with forced ventilation
            # (as in cabin life support airflow 3 cm/s), low-speed flow sustains spread
            g_factor = 0.85 * (ventilation_velocity_cm_s / 3.0)
        elif "lunar" in canonical_g:
            g_factor = 0.95
        elif "mars" in canonical_g:
            g_factor = 1.05
        elif "hyper" in canonical_g:
            g_factor = 1.40
        else:
            g_factor = 1.20  # terrestrial 1g buoyant upward flame acceleration

        # Predicted burn length calculation
        if o2_delta < -2.0:
            predicted_burn_length_cm = round(max(1.0, 4.0 + o2_delta * 0.8), 2)
            dripping_observed = False
        elif o2_delta <= 0.0:
            predicted_burn_length_cm = round(max(3.0, 8.5 + o2_delta * 2.0), 2)
            dripping_observed = profile.dripping_propensity == "high" and "micro" not in canonical_g
        else:
            raw_len = (8.5 + o2_delta * 3.2 * p_factor * t_factor * g_factor)
            predicted_burn_length_cm = round(min(30.0, raw_len), 2)
            dripping_observed = profile.dripping_propensity in ("high", "low")

        # NASA-STD-6001B Test 1: Upward Flame Propagation Assessment
        test_1_pass = (predicted_burn_length_cm < cls.TEST_1_BURN_LENGTH_LIMIT_CM) and not (
            dripping_observed and profile.dripping_propensity == "high"
        )
        test_1_marginal = (
            not test_1_pass
            and predicted_burn_length_cm < (cls.TEST_1_BURN_LENGTH_LIMIT_CM + 2.5)
            and not dripping_observed
        )

        test_1_status = "PASS" if test_1_pass else ("MARGINAL" if test_1_marginal else "FAIL")

        # NASA-STD-6001B Test 7: Heat Release Rate (Cone Calorimeter / Micro-Calorimetry)
        # Peak HRR estimation in kW/m² with char-barrier attenuation
        base_hrr = (profile.heat_of_combustion_mj_kg * 3.0) * max(0.1, (oxygen_percentage / 21.0)) * p_factor
        if profile.char_forming:
            base_hrr *= 0.55  # Protective carbonaceous char layer insulates substrate
        else:
            base_hrr *= 1.35  # Non-charring polymers regress and vaporize directly
        peak_hrr_kw_m2 = round(min(350.0, max(5.0, base_hrr)), 1)

        test_7_pass = peak_hrr_kw_m2 < cls.TEST_7_PEAK_HRR_LIMIT_KW_M2
        test_7_status = "PASS" if test_7_pass else "FAIL"

        # Overall Spacecraft Fire Safety Determination
        if test_1_status == "PASS" and test_7_status == "PASS":
            overall_status = "COMPLIANT"
            recommendation = (
                f"Material {profile.name} meets NASA-STD-6001B Test 1 and Test 7 criteria under "
                f"{oxygen_percentage}% O2 at {pressure_kpa} kPa. Approved for cabin usage."
            )
        elif test_1_status in ("PASS", "MARGINAL") and test_7_status == "PASS":
            overall_status = "RESTRICTED_USE"
            recommendation = (
                f"Material {profile.name} exhibits marginal burn propagation ({predicted_burn_length_cm} cm). "
                f"Requires formal NASA Materials and Processes (M&P) Engineering Waiver."
            )
        else:
            overall_status = "NON_COMPLIANT"
            recommendation = (
                f"Material {profile.name} exceeds NASA-STD-6001B flammability thresholds (Burn Length: {predicted_burn_length_cm} cm, "
                f"Peak HRR: {peak_hrr_kw_m2} kW/m²). Unacceptable for flight cabin interior without secondary fire barrier."
            )

        return {
            "material_name": profile.name,
            "chemical_formula": profile.chemical_formula,
            "test_conditions": {
                "oxygen_percentage": oxygen_percentage,
                "pressure_kpa": pressure_kpa,
                "sample_thickness_mm": thickness_mm,
                "gravity_level": canonical_g,
                "ventilation_velocity_cm_s": ventilation_velocity_cm_s,
            },
            "limiting_oxygen_index": loi,
            "oxygen_margin_pct": round(loi - oxygen_percentage, 1),
            "test_1_upward_propagation": {
                "status": test_1_status,
                "burn_length_cm": predicted_burn_length_cm,
                "burn_length_limit_cm": cls.TEST_1_BURN_LENGTH_LIMIT_CM,
                "dripping_particles": dripping_observed,
            },
            "test_7_heat_release": {
                "status": test_7_status,
                "peak_hrr_kw_m2": peak_hrr_kw_m2,
                "peak_hrr_limit_kw_m2": cls.TEST_7_PEAK_HRR_LIMIT_KW_M2,
                "heat_of_combustion_mj_kg": profile.heat_of_combustion_mj_kg,
                "char_forming": profile.char_forming,
            },
            "overall_compliance": overall_status,
            "safety_recommendation": recommendation,
        }
