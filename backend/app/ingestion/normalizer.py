"""
Mathematical SI Unit Normalization Engine & Strict Non-Zero NULL Policy.
Enforces deterministic conversions and physical validity bounds documented in:
docs/NASA_RESEARCH_LOG.md Section 4 & Section 5.
Supports dual-mode dispatch: single-metric tuple normalization and dictionary normalization.
"""

import math
import re
from typing import Any, Dict, Optional, Set, Tuple, Union

try:
    from pint import UnitRegistry
    ureg = UnitRegistry()
    Q_ = ureg.Quantity
except ImportError:
    ureg = None
    Q_ = None

# Canonical tokens representing missing or unmeasured data in NASA flight logs
NULL_TOKENS: Set[str] = {
    "–",   # Unicode en-dash
    "—",   # Unicode em-dash
    "-",   # ASCII hyphen-minus
    "--",
    "---",
    "n/a",
    "na",
    "null",
    "none",
    "nd",
    "nil",
    "unmeasured",
    "unobserved",
    "uncalibrated",
    "missing",
    "not tracked",
    "not recorded",
    "unrecorded",
    "",
}

# Physical boundary constraints (SI units)
PHYSICAL_BOUNDS = {
    "pressure_pa": (1.0e3, 1.0e7),          # 1 kPa to 10 MPa
    "temperature_k": (150.0, 3500.0),       # 150 K to 3500 K
    "diameter_m": (1.0e-5, 0.1),            # 10 um to 10 cm
    "velocity_m_s": (0.0, 50.0),            # 0 to 50 m/s
    "burning_rate_m2_s": (1.0e-9, 1.0e-4),  # 0.001 to 100 mm^2/s
    "flow_rate_m3_s": (0.0, 1.0e-3),        # 0 to 1 L/s
    "acceleration_m_s2": (0.0, 15.0),       # microgravity to hypergravity
    "mole_fraction": (0.0, 1.0),
}


def is_null_or_unobserved(val: Any) -> bool:
    """
    Checks if a raw value token represents a missing, unobserved, or unrecorded measurement.
    Strictly bans zero substitution: 0.0 is a legitimate physical observation, NOT a missing value!
    """
    if val is None:
        return True
    if isinstance(val, (int, float)):
        return math.isnan(val)
    if isinstance(val, str):
        cleaned = val.strip().lower()
        return cleaned in NULL_TOKENS
    return False


def parse_float_token(val: Any) -> Optional[float]:
    """Extracts a floating point number from a raw token, returning None if unobserved/invalid."""
    if is_null_or_unobserved(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.strip().replace(",", "")
        match = re.search(r"[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?", cleaned)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
    return None


def convert_pressure_to_pa(val: Any, unit: str = "psi") -> Optional[float]:
    """
    Converts pressure measurement to Pascals (Pa).
    Supported raw units: psi, psia, atm, mmhg, torr, bar, kpa, pa.
    """
    num = parse_float_token(val)
    if num is None:
        return None
    u = unit.strip().lower()
    if u in ("psi", "psia"):
        return num * 6894.757293
    elif u == "atm":
        return num * 101325.0
    elif u in ("mmhg", "torr"):
        return num * (101325.0 / 760.0)
    elif u == "bar":
        return num * 100000.0
    elif u == "kpa":
        return num * 1000.0
    elif u == "pa":
        return num
    raise ValueError(f"Unsupported pressure unit: {unit}")


def convert_burning_rate_to_m2_s(val: Any, unit: str = "mm^2/s") -> Optional[float]:
    """
    Converts droplet burning rate constant K to m^2/s.
    Supported raw units: mm^2/s, mm2/s, cm^2/s, cm2/s, m^2/s, m2/s.
    """
    num = parse_float_token(val)
    if num is None:
        return None
    u = unit.strip().lower().replace(" ", "")
    if u in ("mm^2/s", "mm2/s"):
        return num * 1.0e-6
    elif u in ("cm^2/s", "cm2/s"):
        return num * 1.0e-4
    elif u in ("m^2/s", "m2/s"):
        return num
    raise ValueError(f"Unsupported burning rate unit: {unit}")


def convert_velocity_to_m_s(val: Any, unit: str = "cm/s") -> Optional[float]:
    """
    Converts flow or flame spread velocity to m/s.
    Supported raw units: cm/s, mm/s, in/s, m/s.
    """
    num = parse_float_token(val)
    if num is None:
        return None
    u = unit.strip().lower()
    if u == "cm/s":
        return num * 0.01
    elif u == "mm/s":
        return num * 0.001
    elif u in ("in/s", "ips"):
        return num * 0.0254
    elif u == "m/s":
        return num
    raise ValueError(f"Unsupported velocity unit: {unit}")


def convert_length_to_m(val: Any, unit: str = "mm") -> Optional[float]:
    """
    Converts diameter, flame height, or length to meters (m).
    Supported raw units: mm, in, inch, inches, um, μm, micron, microns, m, cm.
    """
    num = parse_float_token(val)
    if num is None:
        return None
    u = unit.strip().lower()
    if u == "mm":
        return num * 0.001
    elif u in ("in", "inch", "inches"):
        return num * 0.0254
    elif u in ("um", "μm", "micron", "microns"):
        return num * 1.0e-6
    elif u == "cm":
        return num * 0.01
    elif u == "m":
        return num
    raise ValueError(f"Unsupported length unit: {unit}")


def convert_flow_rate_to_m3_s(val: Any, unit: str = "sccm") -> Optional[float]:
    """
    Converts volumetric flow rate to m^3/s.
    Supported raw units: sccm (standard cm^3/min), slpm (standard L/min), m^3/s.
    """
    num = parse_float_token(val)
    if num is None:
        return None
    u = unit.strip().lower()
    if u == "sccm":
        return num * (1.0e-6 / 60.0)
    elif u == "slpm":
        return num * (1.0e-3 / 60.0)
    elif u in ("m^3/s", "m3/s"):
        return num
    raise ValueError(f"Unsupported flow rate unit: {unit}")


def convert_temperature_to_kelvin(val: Any, unit: str = "degc") -> Optional[float]:
    """
    Converts temperature to Kelvin (K).
    Supported raw units: degc, °c, c, degf, °f, f, degr, °r, r, k.
    """
    num = parse_float_token(val)
    if num is None:
        return None
    u = unit.strip().lower()
    if u in ("degc", "°c", "c"):
        return num + 273.15
    elif u in ("degf", "°f", "f"):
        return (num - 32.0) * (5.0 / 9.0) + 273.15
    elif u in ("degr", "°r", "r"):
        return num * (5.0 / 9.0)
    elif u == "k":
        return num
    raise ValueError(f"Unsupported temperature unit: {unit}")


def convert_mole_fraction(val: Any, unit: str = "%") -> Optional[float]:
    """Converts volume or molar percentage to dimensionless fraction (0.0 to 1.0)."""
    num = parse_float_token(val)
    if num is None:
        return None
    u = unit.strip().lower()
    if u in ("%", "vol%", "percent"):
        return num / 100.0
    elif u in ("fraction", "dimensionless", "mol/mol"):
        return num
    return num


def normalize_to_si(
    metric_or_dict: Union[str, Dict[str, Any]],
    val_raw: Any = None,
    unit_raw: Optional[str] = None
) -> Union[Tuple[Optional[float], str, str, str], Dict[str, Any]]:
    """
    Dual-mode master SI normalizer.
    Mode 1 (Single Metric): normalize_to_si(metric_name, val_raw, unit_raw) -> (val_si, unit_si, method, status)
    Mode 2 (Dict): normalize_to_si(measurements_dict) -> dict of normalized measurements
    """
    # Mode 2: Dict normalization
    if isinstance(metric_or_dict, dict) and val_raw is None:
        raw_m = metric_or_dict
        si_m: Dict[str, Any] = {}
        for k, v in raw_m.items():
            if v is None:
                si_m[f"{k}_si"] = None
            elif isinstance(v, dict):
                raw_val = v.get("raw")
                raw_unit = v.get("unit", "")
                if is_null_or_unobserved(raw_val):
                    si_m[f"{k}_si"] = None
                else:
                    norm_val, norm_u, _, _ = normalize_to_si(k, raw_val, raw_unit)
                    clean_u = norm_u.replace("/", "_").replace("^", "")
                    si_m[f"{k}_{clean_u}"] = norm_val
            else:
                norm_val, norm_u, _, _ = normalize_to_si(k, v, None)
                si_m[f"{k}_si"] = norm_val
        return si_m

    # Mode 1: Single Metric Normalization
    metric_name = str(metric_or_dict)
    if is_null_or_unobserved(val_raw):
        m_lower = metric_name.lower()
        if "pressure" in m_lower:
            si_u = "Pa"
        elif "burning_rate" in m_lower or "_k" in m_lower:
            si_u = "m^2/s"
        elif "velocity" in m_lower or "spread_rate" in m_lower or "flow_velocity" in m_lower:
            si_u = "m/s"
        elif "diameter" in m_lower or "height" in m_lower or "length" in m_lower:
            si_u = "m"
        elif "flow_rate" in m_lower:
            si_u = "m^3/s"
        elif "temperature" in m_lower:
            si_u = "K"
        elif "flux" in m_lower:
            si_u = "W/m^2"
        elif "duration" in m_lower or "time" in m_lower:
            si_u = "s"
        elif "fraction" in m_lower or "percentage" in m_lower or "concentration" in m_lower:
            si_u = "dimensionless"
        else:
            si_u = "dimensionless"
        return None, si_u, "null_preservation", "MISSING_DATA"

    u = (unit_raw or "").strip().lower()
    m_lower = metric_name.lower()

    if "pressure" in m_lower:
        unit_target = u if u else "psi"
        val_si = convert_pressure_to_pa(val_raw, unit_target)
        method = f"{unit_target} -> Pa"
        unit_si = "Pa"
        valid = is_in_bounds("pressure_pa", val_si)

    elif "burning_rate" in m_lower or (m_lower.endswith("_k") and "mm2" in u):
        unit_target = u if u else "mm^2/s"
        val_si = convert_burning_rate_to_m2_s(val_raw, unit_target)
        method = f"{unit_target} -> m^2/s"
        unit_si = "m^2/s"
        valid = is_in_bounds("burning_rate_m2_s", val_si)

    elif "velocity" in m_lower or "spread_rate" in m_lower:
        unit_target = u if u else "cm/s"
        val_si = convert_velocity_to_m_s(val_raw, unit_target)
        method = f"{unit_target} -> m/s"
        unit_si = "m/s"
        valid = is_in_bounds("velocity_m_s", val_si)

    elif "diameter" in m_lower or "height" in m_lower or "length" in m_lower:
        unit_target = u if u else "mm"
        val_si = convert_length_to_m(val_raw, unit_target)
        method = f"{unit_target} -> m"
        unit_si = "m"
        valid = is_in_bounds("diameter_m", val_si)

    elif "flow_rate" in m_lower:
        unit_target = u if u else "sccm"
        val_si = convert_flow_rate_to_m3_s(val_raw, unit_target)
        method = f"{unit_target} -> m^3/s"
        unit_si = "m^3/s"
        valid = is_in_bounds("flow_rate_m3_s", val_si)

    elif "temperature" in m_lower:
        unit_target = u if u else "degc"
        val_si = convert_temperature_to_kelvin(val_raw, unit_target)
        method = f"{unit_target} -> K"
        unit_si = "K"
        valid = is_in_bounds("temperature_k", val_si)

    elif "duration" in m_lower or "time" in m_lower:
        num = parse_float_token(val_raw)
        val_si = num
        method = "seconds -> s"
        unit_si = "s"
        valid = (val_si is not None and val_si >= 0.0)

    elif "oxygen" in m_lower or "concentration" in m_lower or "mole_fraction" in m_lower:
        unit_target = u if u else "%"
        val_si = convert_mole_fraction(val_raw, unit_target)
        method = f"{unit_target} -> fraction"
        unit_si = "dimensionless"
        valid = is_in_bounds("mole_fraction", val_si)

    else:
        val_si = parse_float_token(val_raw)
        unit_si = unit_raw or "dimensionless"
        method = "identity"
        valid = True

    status = "VALID" if valid else "OUT_OF_BOUNDS"
    return val_si, unit_si, method, status


def is_in_bounds(bound_key: str, val_si: Optional[float]) -> bool:
    """Checks whether an SI value is within expected scientific physical boundaries."""
    if val_si is None:
        return True
    bounds = PHYSICAL_BOUNDS.get(bound_key)
    if not bounds:
        return True
    low, high = bounds
    return low <= val_si <= high
