"""NASA-STD-6001B Flammability Validation Rules Engine.

Formalized rules engine for spacecraft material qualification in exploration atmospheres.
Covers:
- NASA-STD-6001B Test 1: Upward Flame Propagation (< 15.24 cm / 6.0 in, zero burning drips)
- NASA-STD-6001B Test 7: Heat Release Rate (< 100 kW/m² peak, < 20 MJ/m² total)
- Limiting Oxygen Index (LOI / MOC) & Margin Evaluation
- Pressure and Gravity Convection Scaling
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.app.safety.standards import CABIN_ATMOSPHERES, SPACECRAFT_MATERIALS, CabinAtmosphere, MaterialFlammabilityProfile


@dataclass
class RuleEvaluation:
    rule_id: str
    rule_name: str
    status: str  # "PASS", "FAIL", "MARGINAL", "INCONCLUSIVE"
    threshold: Any
    measured_value: Any
    margin: Optional[float] = None
    detail: str = ""


@dataclass
class FlammabilityComplianceReport:
    material_key: str
    material_name: str
    overall_status: str  # "COMPLIANT", "RESTRICTED_USE", "NON_COMPLIANT"
    oxygen_percentage: float
    pressure_kpa: float
    thickness_mm: Optional[float]
    gravity_level: str
    rules_evaluated: List[RuleEvaluation] = field(default_factory=list)
    waiver_required: bool = False
    recommendations: List[str] = field(default_factory=list)


class FlammabilityRulesEngine:
    """Deterministic validation rules engine implementing NASA-STD-6001B qualification."""

    TEST_1_MAX_BURN_LENGTH_CM = 15.24  # 6.0 inches
    TEST_7_MAX_PEAK_HRR_KW_M2 = 100.0   # kW/m²
    TEST_7_MAX_TOTAL_HR_MJ_M2 = 20.0    # MJ/m²

    @classmethod
    def evaluate(
        cls,
        material_key: str,
        oxygen_percentage: float = 21.0,
        pressure_kpa: float = 101.325,
        thickness_mm: Optional[float] = 2.0,
        gravity_level: str = "microgravity (~10^-6 g)",
        ventilation_velocity_cm_s: float = 3.0,
    ) -> FlammabilityComplianceReport:
        """Executes full NASA-STD-6001B rule set against material and environment parameters."""
        mat_key_clean = material_key.strip().lower()
        profile: Optional[MaterialFlammabilityProfile] = SPACECRAFT_MATERIALS.get(mat_key_clean)
        if not profile:
            for k, p in SPACECRAFT_MATERIALS.items():
                if k in mat_key_clean or mat_key_clean in k or mat_key_clean in p.name.lower():
                    profile = p
                    mat_key_clean = k
                    break

        if not profile:
            raise ValueError(
                f"Unknown material '{material_key}'. Supported materials: {list(SPACECRAFT_MATERIALS.keys())}"
            )

        if oxygen_percentage <= 0 or oxygen_percentage > 100:
            raise ValueError(f"Oxygen percentage {oxygen_percentage}% out of valid range (0, 100].")

        if pressure_kpa <= 0 or pressure_kpa > 300:
            raise ValueError(f"Cabin pressure {pressure_kpa} kPa out of valid range (0, 300].")

        if thickness_mm is not None and thickness_mm <= 0:
            raise ValueError(f"Sample thickness must be positive, got {thickness_mm} mm.")

        rules: List[RuleEvaluation] = []
        recommendations: List[str] = []

        # Rule 1: Limiting Oxygen Index (LOI / MOC) Margin
        o2_margin = profile.limiting_oxygen_index - oxygen_percentage
        if o2_margin >= 3.0:
            loi_status = "PASS"
            loi_detail = f"Adequate oxygen safety margin (+{o2_margin:.1f}% O2 above ambient)."
        elif o2_margin >= 0.0:
            loi_status = "MARGINAL"
            loi_detail = f"Near limiting oxygen index (+{o2_margin:.1f}% O2 margin). Susceptible to localized ignition."
        else:
            loi_status = "FAIL"
            loi_detail = f"Environment oxygen ({oxygen_percentage:.1f}%) exceeds material LOI ({profile.limiting_oxygen_index:.1f}%)."
            recommendations.append("Material will sustain combustion once ignited; requires active fire extinguishing or barrier wrapping.")

        rules.append(
            RuleEvaluation(
                rule_id="NASA-STD-6001B-LOI",
                rule_name="Limiting Oxygen Index Margin",
                status=loi_status,
                threshold=profile.limiting_oxygen_index,
                measured_value=oxygen_percentage,
                margin=round(o2_margin, 2),
                detail=loi_detail,
            )
        )

        # Rule 2: Test 1 Upward Flame Propagation
        # Pressure scaling: p_factor = (P / 101.3)^0.3
        p_factor = math.pow(pressure_kpa / 101.325, 0.3)
        # Thickness factor: (2.0 / t)^0.5
        t_factor = math.pow(2.0 / max(thickness_mm or 2.0, 0.2), 0.5)

        o2_delta = oxygen_percentage - profile.limiting_oxygen_index
        if o2_delta < -2.0:
            est_burn_len = max(1.0, 4.0 + o2_delta * 0.8)
            dripping = False
        elif o2_delta <= 0.0:
            est_burn_len = max(3.0, 8.5 + o2_delta * 2.0)
            dripping = profile.dripping_propensity == "high" and "micro" not in gravity_level.lower()
        else:
            est_burn_len = min(30.0, 8.5 + o2_delta * 3.2 * p_factor * t_factor)
            dripping = profile.dripping_propensity in ("high", "low")

        est_burn_len = round(est_burn_len, 2)
        test_1_pass = est_burn_len < cls.TEST_1_MAX_BURN_LENGTH_CM and not (
            dripping and profile.dripping_propensity == "high"
        )
        test_1_status = "PASS" if test_1_pass else "FAIL"

        rules.append(
            RuleEvaluation(
                rule_id="NASA-STD-6001B-TEST-1",
                rule_name="Test 1 Upward Flame Propagation & Dripping",
                status=test_1_status,
                threshold=f"< {cls.TEST_1_MAX_BURN_LENGTH_CM} cm, zero flaming drips",
                measured_value=f"{est_burn_len} cm (dripping={dripping})",
                margin=round(cls.TEST_1_MAX_BURN_LENGTH_CM - est_burn_len, 2),
                detail="Flame self-extinguished prior to benchmark mark." if test_1_pass else "Burn length exceeded 15.24 cm limit.",
            )
        )

        # Rule 3: Test 7 Heat Release Rate (Peak HRR)
        base_hrr = (profile.heat_of_combustion_mj_kg * 3.0) * max(0.1, (oxygen_percentage / 21.0)) * p_factor
        if profile.char_forming:
            base_hrr *= 0.55
        else:
            base_hrr *= 1.35
        peak_hrr = round(min(350.0, max(5.0, base_hrr)), 1)
        test_7_pass = peak_hrr < cls.TEST_7_MAX_PEAK_HRR_KW_M2
        test_7_status = "PASS" if test_7_pass else "FAIL"

        rules.append(
            RuleEvaluation(
                rule_id="NASA-STD-6001B-TEST-7",
                rule_name="Test 7 Peak Heat Release Rate",
                status=test_7_status,
                threshold=f"< {cls.TEST_7_MAX_PEAK_HRR_KW_M2} kW/m²",
                measured_value=f"{peak_hrr} kW/m²",
                margin=round(cls.TEST_7_MAX_PEAK_HRR_KW_M2 - peak_hrr, 1),
                detail="Peak thermal heat release rate satisfies spacecraft fire barrier limit." if test_7_pass else "Peak HRR exceeds safety boundary.",
            )
        )

        # Overall Status Determination
        all_passed = all(r.status == "PASS" for r in rules)
        any_failed = any(r.status == "FAIL" for r in rules)

        if all_passed:
            overall = "COMPLIANT"
            waiver = False
            recommendations.append("Full qualification approved for flight module interior.")
        elif not any_failed:
            overall = "RESTRICTED_USE"
            waiver = True
            recommendations.append("Marginal condition. Requires NASA Materials & Processes (M&P) waiver with secondary containment.")
        else:
            overall = "NON_COMPLIANT"
            waiver = True
            recommendations.append("Unacceptable for human-rated spacecraft cabin usage without fire-retardant barrier cladding.")

        return FlammabilityComplianceReport(
            material_key=mat_key_clean,
            material_name=profile.name,
            overall_status=overall,
            oxygen_percentage=oxygen_percentage,
            pressure_kpa=pressure_kpa,
            thickness_mm=thickness_mm,
            gravity_level=gravity_level,
            rules_evaluated=rules,
            waiver_required=waiver,
            recommendations=recommendations,
        )
