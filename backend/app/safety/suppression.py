"""Cabin Fire Suppression & Damper Simulator Engine (Requirement R2 / Upgrade E-12).

Simulates dynamic microgravity fire suppression kinetics for three authentic spacecraft
emergency response protocols:
1. Ventilation Damper Isolation: forced airflow shutdown reducing u_vent to pure molecular diffusion
   (u_diff ≈ 0.01 cm/s), triggering radiative hot-flame extinction while surging residence time.
2. Halon 1301 / FK-5-1-12 Chemical Agent Release: rapid catalytic radical scavenging (eta_scavenge -> 1.0)
   and thermal quenching below flash point (< 315 K), driving residual radical HRR to 0 W.
3. Nitrogen (N2) Flooding: hypobaric dilution lowering cabin O2 below minimum extinguishing concentration (MOC),
   extinguishing the flame but leaving rekindling vulnerability if re-ventilated while warm.

Coupled with RekindleWarningEngine and NASA-STD-6001B spacecraft materials catalog.
"""

from __future__ import annotations

import math
from typing import Any

from backend.app.kinetics.rekindle_warning import (
    FUEL_ALIASES,
    LTC_FUEL_PROFILES,
    R_GAS_CONSTANT,
    RekindleWarningEngine,
)
from backend.app.safety.standards import SPACECRAFT_MATERIALS
from backend.app.schemas.suppression import (
    CabinSuppressionRequest,
    CabinSuppressionResponse,
    SuppressionDecayPoint,
)

# Physical constants and boundary floors
MIN_VELOCITY_FLOOR_M_S: float = 1e-4  # 0.01 cm/s physical diffusion floor in microgravity
AMBIENT_CABIN_TEMP_K: float = 293.15  # 20.0 °C nominal spacecraft cabin ambient
INITIAL_RADICAL_POOL_HRR_W: float = 65.0  # Calibrated to FLEX n-heptane cool-flame radical release
INITIAL_HOT_FLAME_HRR_KW: float = 0.85  # Baseline hot-flame heat release rate in kW

# Chemical agent suppression parameters (FK-5-1-12 / Halon 1301)
AGENT_DESIGN_CONC_VOL_PCT: float = 5.8  # Design vol % in cabin volume
AGENT_EXTINCTION_CONC_VOL_PCT: float = 4.5  # Extinction threshold vol %
AGENT_DISCHARGE_TAU_S: float = 0.5  # Injection time constant
AGENT_THERMAL_QUENCH_TAU_S: float = 1.2  # Endothermic cooling time constant

# Damper closure parameters
DAMPER_CLOSURE_TAU_S: float = 0.8  # Mechanical butterfly damper closure time
DAMPER_RADIATIVE_EXTINCTION_TIME_S: float = 14.5  # Microgravity radiative extinction time
DAMPER_COOL_FLAME_PLATEAU_K: float = 705.0  # Cool flame NTC temperature sustained by residual radical pool
DAMPER_RADICAL_DECAY_TAU_S: float = 18.0  # Cool-flame radical lifetime under damper isolation

# Nitrogen flooding parameters
N2_FLOODING_TURNOVER_TAU_S: float = 4.5  # Stirred chamber turnover time constant (~7.2s to alkane MOC)
N2_COOLING_TAU_S: float = 16.0  # Cold N2 gas cooling time constant
DEFAULT_MOC_O2_PERCENTAGE: float = 11.8  # Minimum Oxygen Concentration for alkane fuels


class CabinSuppressionEngine:
    """Transient physical simulation engine for spacecraft cabin fire emergency response actions."""

    @classmethod
    def resolve_fuel_or_material(cls, identifier: str) -> dict[str, Any]:
        """Resolves fuel or spacecraft material properties from LTC or NASA-STD catalogs.

        Supports liquid/gas fuels ('n-heptane', 'n-octane', 'n-decane', 'methanol', etc.)
        and solid spacecraft materials ('pmma', 'nomex', 'delrin', 'polycarbonate', 'teflon', 'kevlar').
        """
        raw = identifier.strip().lower().replace("_", "-")

        # 1. Check solid spacecraft materials catalog
        mat_key = raw.replace("-", "")
        if mat_key in SPACECRAFT_MATERIALS:
            mat = SPACECRAFT_MATERIALS[mat_key]
            return {
                "name": mat.name,
                "formula": mat.chemical_formula,
                "supports_ltc": False,
                "flash_point_k": 550.0,  # Pyrolysis / ignition threshold proxy
                "limiting_oxygen_index": mat.limiting_oxygen_index,
                "heat_of_combustion_mj_kg": mat.heat_of_combustion_mj_kg,
                "e_ltc_j_mol": None,
                "a_ltc_s_inv": None,
                "is_solid_material": True,
            }

        # 2. Check LTC fuel profiles and aliases
        alias_key = FUEL_ALIASES.get(raw, raw)
        if alias_key in LTC_FUEL_PROFILES:
            profile = LTC_FUEL_PROFILES[alias_key]
            return {
                "name": profile["name"],
                "formula": profile["formula"],
                "supports_ltc": profile["supports_ltc"],
                "flash_point_k": profile["flash_point_k"],
                "limiting_oxygen_index": DEFAULT_MOC_O2_PERCENTAGE,
                "heat_of_combustion_mj_kg": 44.6,  # Typical alkane standard
                "e_ltc_j_mol": profile["e_ltc_j_mol"],
                "a_ltc_s_inv": profile["a_ltc_s_inv"],
                "is_solid_material": False,
            }

        # Fallback for standard fuels matching common names
        for standard_key in LTC_FUEL_PROFILES:
            if standard_key in raw or raw in standard_key:
                profile = LTC_FUEL_PROFILES[standard_key]
                return {
                    "name": profile["name"],
                    "formula": profile["formula"],
                    "supports_ltc": profile["supports_ltc"],
                    "flash_point_k": profile["flash_point_k"],
                    "limiting_oxygen_index": DEFAULT_MOC_O2_PERCENTAGE,
                    "heat_of_combustion_mj_kg": 44.6,
                    "e_ltc_j_mol": profile["e_ltc_j_mol"],
                    "a_ltc_s_inv": profile["a_ltc_s_inv"],
                    "is_solid_material": False,
                }

        supported_fuels = list(LTC_FUEL_PROFILES.keys()) + list(SPACECRAFT_MATERIALS.keys())
        raise ValueError(
            f"Unsupported fuel or material '{identifier}'. Supported options: {supported_fuels}"
        )

    @classmethod
    def simulate(cls, request: CabinSuppressionRequest) -> CabinSuppressionResponse:
        """Executes transient fire suppression simulation across the requested duration."""
        props = cls.resolve_fuel_or_material(request.fuel)

        # Track active actions
        actions: list[str] = []
        if request.damper_isolated:
            actions.append("DAMPER_ISOLATION")
        if request.chemical_agent_released:
            actions.append("CHEMICAL_AGENT_RELEASE")
        if request.n2_flooding_active:
            actions.append("N2_FLOODING")
        if not actions:
            actions.append("NO_ACTION")

        # Time parameters
        duration = request.simulation_duration_s
        dt = request.time_step_s
        n_steps = round(duration / dt) + 1

        u0_cm_s = request.initial_ventilation_velocity_cm_s
        o2_0 = request.initial_o2_percentage
        t0_k = request.initial_fuel_temperature_k
        char_len = request.characteristic_length_m
        flash_point_k = props["flash_point_k"]
        moc_o2 = props["limiting_oxygen_index"]
        supports_ltc = props["supports_ltc"]
        e_ltc = props["e_ltc_j_mol"]
        a_ltc = props["a_ltc_s_inv"]

        # Extinction analytical timing estimate
        extinction_time: float | None = None
        extinction_mechanism = "No suppression actions applied; steady-state flame continues."

        if request.chemical_agent_released and request.damper_isolated and request.n2_flooding_active:
            extinction_time = 0.8
            extinction_mechanism = (
                "Combined full-spectrum suppression: forced ventilation cutoff, "
                "rapid catalytic radical scavenging, and hypobaric N2 dilution."
            )
        elif request.chemical_agent_released and request.damper_isolated:
            extinction_time = 1.1
            extinction_mechanism = (
                "Catalytic radical scavenging combined with forced convection cutoff."
            )
        elif request.chemical_agent_released:
            extinction_time = 1.5
            extinction_mechanism = (
                f"{request.chemical_agent_type} catalytic radical scavenging and endothermic thermal quenching."
            )
        elif request.n2_flooding_active and request.damper_isolated:
            extinction_time = 5.2
            extinction_mechanism = (
                "Convective isolation coupled with nitrogen dilution starving reaction zone below MOC."
            )
        elif request.n2_flooding_active:
            # Analytical stirred chamber extinction time
            target_o2 = request.n2_target_o2_percentage
            if target_o2 < moc_o2 and o2_0 > moc_o2:
                extinction_time = round(
                    N2_FLOODING_TURNOVER_TAU_S * math.log((o2_0 - target_o2) / (moc_o2 - target_o2)),
                    1,
                )
            else:
                extinction_time = 7.2
            extinction_mechanism = (
                f"Hypobaric nitrogen flooding reducing cabin O2 below MOC ({moc_o2:.1f}%)."
            )
        elif request.damper_isolated:
            extinction_time = DAMPER_RADIATIVE_EXTINCTION_TIME_S
            extinction_mechanism = (
                "Forced convection cutoff inducing microgravity radiative heat loss extinction."
            )

        decay_curve: list[SuppressionDecayPoint] = []
        extinction_detected_t: float | None = None

        for i in range(n_steps):
            t = round(i * dt, 4)

            # 1. Ventilation velocity (cm/s)
            if request.damper_isolated:
                # Exponential decay towards diffusion floor u_diff = 0.01 cm/s
                u_decay = u0_cm_s * math.exp(-t / DAMPER_CLOSURE_TAU_S)
                u_vent_t = max(0.01, u_decay)
            else:
                u_vent_t = u0_cm_s

            # 2. Chemical agent concentration & radical scavenging efficiency
            if request.chemical_agent_released:
                c_agent_t = AGENT_DESIGN_CONC_VOL_PCT * (1.0 - math.exp(-t / AGENT_DISCHARGE_TAU_S))
                eta_scavenge_t = min(1.0, (c_agent_t / AGENT_EXTINCTION_CONC_VOL_PCT) * 1.2)
            else:
                c_agent_t = 0.0
                eta_scavenge_t = 0.0

            # 3. Oxygen percentage (%)
            if request.n2_flooding_active:
                target_o2 = request.n2_target_o2_percentage
                o2_t = target_o2 + (o2_0 - target_o2) * math.exp(-t / N2_FLOODING_TURNOVER_TAU_S)
            elif request.damper_isolated and not request.chemical_agent_released:
                # Moderate local depletion due to stagnant diffusion consumption
                o2_t = max(14.0, o2_0 - 3.5 * (1.0 - math.exp(-t / 8.0)))
            else:
                o2_t = o2_0

            # 4. Temperature (K)
            if request.chemical_agent_released:
                # Rapid endothermic thermal quench below flash point
                temp_t = AMBIENT_CABIN_TEMP_K + (t0_k - AMBIENT_CABIN_TEMP_K) * math.exp(
                    -t / AGENT_THERMAL_QUENCH_TAU_S
                )
            elif request.n2_flooding_active and request.damper_isolated:
                temp_t = AMBIENT_CABIN_TEMP_K + (t0_k - AMBIENT_CABIN_TEMP_K) * math.exp(
                    -t / (N2_COOLING_TAU_S * 0.8)
                )
            elif request.n2_flooding_active:
                temp_t = AMBIENT_CABIN_TEMP_K + (t0_k - AMBIENT_CABIN_TEMP_K) * math.exp(
                    -t / N2_COOLING_TAU_S
                )
            elif request.damper_isolated:
                # In microgravity, stagnant boundary layer and cool flame heat release sustain NTC plateau
                target_damper_temp = DAMPER_COOL_FLAME_PLATEAU_K if supports_ltc else AMBIENT_CABIN_TEMP_K
                temp_t = target_damper_temp + (t0_k - target_damper_temp) * math.exp(
                    -t / 20.0
                )
            else:
                # Steady-state combustion: minimal cooling
                temp_t = max(t0_k * 0.95, t0_k - 0.5 * t)

            # 5. Extinction check at current time step
            is_extinguished = False
            if extinction_time is not None and t >= extinction_time:
                is_extinguished = True
                if extinction_detected_t is None:
                    extinction_detected_t = t

            # 6. Heat release rates
            # Hot flame HRR in kW
            if is_extinguished:
                hot_hrr_kw = 0.0
            else:
                o2_factor = max(0.0, (o2_t - moc_o2 * 0.5) / (21.0 - moc_o2 * 0.5)) if o2_0 > moc_o2 else 1.0
                u_factor = (u_vent_t / max(u0_cm_s, 0.01)) ** 0.3
                hot_hrr_kw = INITIAL_HOT_FLAME_HRR_KW * o2_factor * u_factor * (1.0 - eta_scavenge_t)
                hot_hrr_kw = max(0.0, hot_hrr_kw)

            # Residual radical HRR in Watts
            if request.chemical_agent_released:
                # Radicals scavenged within 1.5s
                res_hrr_w = INITIAL_RADICAL_POOL_HRR_W * math.exp(-t / 0.4) * (1.0 - eta_scavenge_t)
                if t >= 1.5 or eta_scavenge_t >= 0.98:
                    res_hrr_w = 0.0
            elif request.damper_isolated:
                # Cool flame radical pool decays slowly
                o2_ratio = max(0.0, o2_t / 21.0)
                temp_indicator = 1.0 if temp_t > flash_point_k else 0.0
                res_hrr_w = (
                    INITIAL_RADICAL_POOL_HRR_W
                    * math.exp(-t / DAMPER_RADICAL_DECAY_TAU_S)
                    * o2_ratio
                    * temp_indicator
                )
            elif request.n2_flooding_active:
                o2_ratio = max(0.0, o2_t / 21.0)
                temp_indicator = 1.0 if temp_t > flash_point_k else 0.0
                res_hrr_w = (
                    INITIAL_RADICAL_POOL_HRR_W
                    * math.exp(-t / N2_COOLING_TAU_S)
                    * o2_ratio
                    * temp_indicator
                )
            else:
                # Baseline steady combustion
                res_hrr_w = INITIAL_RADICAL_POOL_HRR_W

            total_hrr_kw = hot_hrr_kw + (res_hrr_w / 1000.0)

            # 7. Cool-flame Damköhler number Da_cool(t)
            u_eff_m_s = max(u_vent_t * 0.01, MIN_VELOCITY_FLOOR_M_S)
            tau_res = char_len / u_eff_m_s

            if supports_ltc and e_ltc is not None and a_ltc is not None and eta_scavenge_t < 0.99:
                exp_arg = -e_ltc / (R_GAS_CONSTANT * temp_t)
                k_ltc = a_ltc * math.exp(exp_arg) if exp_arg > -700.0 else 0.0
                k_eff = k_ltc * math.sqrt(max(0.0, o2_t / 21.0)) * (1.0 - eta_scavenge_t)
                da_cool_t = tau_res * k_eff
            else:
                da_cool_t = 0.0

            # 8. Instantaneous rekindle probability P_rekindle(t)
            if request.chemical_agent_released or temp_t <= flash_point_k or not supports_ltc:
                p_rekindle_t = 0.0
            else:
                exp_sig = -(da_cool_t - 1.0) / 0.20
                if exp_sig > 100.0:
                    p_rekindle_t = 0.0
                elif exp_sig < -100.0:
                    p_rekindle_t = 1.0
                else:
                    p_rekindle_t = 1.0 / (1.0 + math.exp(exp_sig))

            decay_curve.append(
                SuppressionDecayPoint(
                    time_s=t,
                    temperature_k=round(temp_t, 1),
                    heat_release_rate_kw=round(total_hrr_kw, 3),
                    residual_radical_hrr_w=round(res_hrr_w, 2),
                    o2_percentage=round(o2_t, 2),
                    ventilation_velocity_cm_s=round(u_vent_t, 3),
                    agent_concentration_vol_pct=round(c_agent_t, 2),
                    damkohler_cool=round(da_cool_t, 3),
                    rekindle_probability=round(p_rekindle_t, 3),
                )
            )

        # Final state values
        final_pt = decay_curve[-1]
        final_t_k = final_pt.temperature_k
        final_o2 = final_pt.o2_percentage
        final_u_cm_s = final_pt.ventilation_velocity_cm_s
        final_res_hrr_w = final_pt.residual_radical_hrr_w
        final_da_cool = final_pt.damkohler_cool

        # Extinction achievement evaluation
        extinction_achieved = extinction_time is not None and duration >= extinction_time
        transient_ext_time = extinction_time if extinction_achieved else None

        # 9. Rekindling probability upon ventilation restart (P_rekindle,restart)
        # Assesses risk if cabin airflow is restored to restart_ventilation_velocity_cm_s with nominal air
        u_restart_m_s = max(request.restart_ventilation_velocity_cm_s * 0.01, MIN_VELOCITY_FLOOR_M_S)
        tau_res_restart = char_len / u_restart_m_s

        if request.chemical_agent_released:
            # Active radicals destroyed, thermal quench below flash point -> INERT
            da_cool_restart = 0.0
            p_rekindle_restart = 0.0
            rekindle_risk_level = "INERT"
            safe_to_restart = extinction_achieved and (final_t_k <= flash_point_k or final_t_k <= 315.0)
        elif not extinction_achieved:
            # Fire still burning!
            da_cool_restart = final_da_cool
            p_rekindle_restart = 1.0
            rekindle_risk_level = "CRITICAL_REKINDLE_HAZARD"
            safe_to_restart = False
        elif final_t_k <= flash_point_k or not supports_ltc:
            da_cool_restart = 0.0
            p_rekindle_restart = 0.0
            rekindle_risk_level = "INERT"
            safe_to_restart = True
        else:
            # Hot fuel without chemical scavenger: evaluate cool-flame restart kinetics
            exp_arg = -e_ltc / (R_GAS_CONSTANT * final_t_k)
            k_restart = a_ltc * math.exp(exp_arg) if exp_arg > -700.0 else 0.0
            da_cool_restart = tau_res_restart * k_restart
            exp_sig = -(da_cool_restart - 1.0) / 0.20
            if exp_sig > 100.0:
                p_rekindle_restart = 0.0
            elif exp_sig < -100.0:
                p_rekindle_restart = 1.0
            else:
                p_rekindle_restart = 1.0 / (1.0 + math.exp(exp_sig))

            rekindle_risk_level = RekindleWarningEngine.classify_risk(p_rekindle_restart)
            safe_to_restart = p_rekindle_restart < 0.20 and final_t_k <= flash_point_k

        # 10. Operational safety advisories & audit telemetry
        if not extinction_achieved:
            if request.damper_isolated:
                safety_advisory = (
                    "Ventilation damper isolated. Convective cutoff in progress; "
                    "flame is approaching radiative extinction threshold."
                )
                audit_msg = (
                    "DAMPER_ISOLATION_STANDBY: Forced airflow shutdown in progress. "
                    "Hot flame extinction pending (14.5s threshold)."
                )
            elif request.n2_flooding_active:
                safety_advisory = (
                    f"Nitrogen flooding active. Cabin oxygen currently at {final_o2:.1f}%; "
                    "dilution to MOC threshold in progress."
                )
                audit_msg = (
                    f"N2_FLOODING_IN_PROGRESS: Chamber O2 at {final_o2:.1f}%. Dilution below MOC pending."
                )
            else:
                safety_advisory = (
                    "Unmitigated combustion active. Immediate emergency suppression action required."
                )
                audit_msg = (
                    "NO_ACTION_ACTIVE_FIRE: Unmitigated flame propagation in progress. Extinction not achieved."
                )
        elif request.chemical_agent_released:
            safety_advisory = (
                f"{request.chemical_agent_type} successfully scavenged active radicals and quenched "
                f"core temperature to {final_t_k:.1f} K. Safe to restore ventilation."
            )
            audit_msg = (
                f"SUPPRESSION_SUCCESS: Transient extinction achieved in {transient_ext_time:.1f}s. "
                "Permanent inert status confirmed."
            )
        elif request.damper_isolated and not request.n2_flooding_active:
            safety_advisory = (
                "Forced airflow cutoff radiatively quenched visible flame, but residence time surge "
                "sustains cool flame radical pool. DO NOT restart ventilation until fuel cools below flash point."
            )
            audit_msg = (
                f"DAMPER_ISOLATION_STANDBY: Radiative hot-flame extinction at {transient_ext_time:.1f}s. "
                f"Restart rekindle hazard: {rekindle_risk_level} (P={p_rekindle_restart:.2f})."
            )
        elif request.n2_flooding_active:
            safety_advisory = (
                f"Chamber diluted to {final_o2:.1f}% O2 below MOC. Maintain inert N2 blanket until "
                f"core fuel temperature drops below {flash_point_k:.1f} K to prevent restart rekindling."
            )
            audit_msg = (
                f"N2_FLOODING_EXTINCTION: Flame extinguished at {transient_ext_time:.1f}s via hypobaric dilution. "
                f"Rekindle risk on re-oxygenation: {rekindle_risk_level} (P={p_rekindle_restart:.2f})."
            )
        else:
            safety_advisory = (
                "Unmitigated combustion active. Immediate emergency suppression action required."
            )
            audit_msg = (
                "NO_ACTION_ACTIVE_FIRE: Unmitigated flame propagation in progress. Extinction not achieved."
            )

        return CabinSuppressionResponse(
            fuel=props["name"],
            fuel_formula=props["formula"],
            actions_applied=actions,
            extinction_achieved=extinction_achieved,
            transient_extinction_time_s=transient_ext_time,
            extinction_mechanism=extinction_mechanism,
            initial_temperature_k=round(t0_k, 1),
            final_temperature_k=round(final_t_k, 1),
            initial_o2_percentage=round(o2_0, 1),
            final_o2_percentage=round(final_o2, 1),
            initial_ventilation_velocity_cm_s=round(u0_cm_s, 2),
            final_ventilation_velocity_cm_s=round(final_u_cm_s, 3),
            initial_radical_heat_release_w=INITIAL_RADICAL_POOL_HRR_W,
            residual_radical_heat_release_w=round(final_res_hrr_w, 2),
            damkohler_cool_final=round(final_da_cool, 3),
            damkohler_cool_restart=round(da_cool_restart, 3),
            rekindle_probability_restart=round(p_rekindle_restart, 3),
            rekindle_risk_level=rekindle_risk_level,
            safe_to_restart_ventilation=safe_to_restart,
            decay_curve=decay_curve,
            safety_advisory=safety_advisory,
            audit_message=audit_msg,
        )
