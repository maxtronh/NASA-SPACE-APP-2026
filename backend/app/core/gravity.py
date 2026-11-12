"""Gravity regime constants, buoyancy parameter calculations, and convection classification.

Supports microgravity (~10^-6 g), lunar (0.16g), Mars (0.38g), normal gravity (1.0g),
and hypergravity (2g, 5g) combustion regimes.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class GravityLevel(str, Enum):
    MICROGRAVITY = "microgravity (~10^-6 g)"
    LUNAR = "lunar_gravity (0.16 g)"
    MARS = "mars_gravity (0.38 g)"
    NORMAL = "normal_gravity (1.0 g)"
    HYPERGRAVITY_2G = "hypergravity_2g (2.0 g)"
    HYPERGRAVITY_5G = "hypergravity_5g (5.0 g)"


# Approximate acceleration in m/s²
GRAVITY_ACCELERATION_MS2: dict[str, float] = {
    GravityLevel.MICROGRAVITY.value: 9.81e-6,
    GravityLevel.LUNAR.value: 1.62,
    GravityLevel.MARS.value: 3.71,
    GravityLevel.NORMAL.value: 9.80665,
    GravityLevel.HYPERGRAVITY_2G.value: 19.62,
    GravityLevel.HYPERGRAVITY_5G.value: 49.05,
}

# Dimensionless Grashof-scaling buoyancy indicator (normalized to 1.0 for terrestrial 1g)
BUOYANCY_PARAMETERS: dict[str, float] = {
    GravityLevel.MICROGRAVITY.value: 0.000001,
    GravityLevel.LUNAR.value: 0.165,
    GravityLevel.MARS.value: 0.378,
    GravityLevel.NORMAL.value: 1.0,
    GravityLevel.HYPERGRAVITY_2G.value: 2.0,
    GravityLevel.HYPERGRAVITY_5G.value: 5.0,
}


def normalize_gravity_level(gravity_level: str) -> str:
    """Normalizes informal gravity level strings to canonical GravityLevel enum values."""
    if not gravity_level:
        return GravityLevel.MICROGRAVITY.value
    clean = gravity_level.strip().lower()

    if "lunar" in clean or "0.16" in clean:
        return GravityLevel.LUNAR.value
    if "mars" in clean or "0.38" in clean:
        return GravityLevel.MARS.value
    if "5g" in clean or "5.0" in clean:
        return GravityLevel.HYPERGRAVITY_5G.value
    if "hyper" in clean or "2g" in clean or "2.0" in clean:
        return GravityLevel.HYPERGRAVITY_2G.value
    if "normal" in clean or "1g" in clean or "1.0 g" in clean or "earth" in clean or "terrestrial" in clean:
        return GravityLevel.NORMAL.value
    if "micro" in clean or "10^-6" in clean or "freefall" in clean or "0g" in clean or "zero" in clean:
        return GravityLevel.MICROGRAVITY.value

    return clean


def get_gravity_acceleration(gravity_level: str) -> float:
    """Returns effective gravitational acceleration in m/s²."""
    canonical = normalize_gravity_level(gravity_level)
    return GRAVITY_ACCELERATION_MS2.get(canonical, 9.80665)


def calculate_buoyancy_parameter(gravity_level: str) -> float:
    """Returns dimensionless buoyancy parameter (Grashof scaling factor relative to 1g)."""
    canonical = normalize_gravity_level(gravity_level)
    return BUOYANCY_PARAMETERS.get(canonical, 1.0)


def classify_convection_regime(gravity_level: str) -> str:
    """Classifies natural convection strength: 'suppressed', 'moderate', or 'strong'."""
    canonical = normalize_gravity_level(gravity_level)
    if canonical == GravityLevel.MICROGRAVITY.value:
        return "suppressed"
    if canonical in (GravityLevel.LUNAR.value, GravityLevel.MARS.value):
        return "moderate"
    return "strong"


def classify_flame_geometry(gravity_level: str) -> str:
    """Classifies characteristic flame geometry: 'spherical', 'teardrop', or 'plume'."""
    canonical = normalize_gravity_level(gravity_level)
    if canonical == GravityLevel.MICROGRAVITY.value:
        return "spherical"
    if canonical in (GravityLevel.LUNAR.value, GravityLevel.MARS.value):
        return "teardrop"
    return "plume"


def classify_soot_behavior(gravity_level: str) -> str:
    """Classifies soot particulate residence behavior: 'trapped', 'flickering', or 'rising'."""
    canonical = normalize_gravity_level(gravity_level)
    if canonical == GravityLevel.MICROGRAVITY.value:
        return "trapped"
    if canonical in (GravityLevel.LUNAR.value, GravityLevel.MARS.value):
        return "flickering"
    return "rising"


def get_gravity_regime_category(gravity_level: str) -> str:
    """Categorizes gravity regime into 'microgravity', 'partial_gravity', 'normal_gravity', or 'hypergravity'."""
    canonical = normalize_gravity_level(gravity_level)
    if canonical == GravityLevel.MICROGRAVITY.value:
        return "microgravity"
    if canonical in (GravityLevel.LUNAR.value, GravityLevel.MARS.value):
        return "partial_gravity"
    if canonical == GravityLevel.NORMAL.value:
        return "normal_gravity"
    return "hypergravity"


def generate_buoyancy_warning(gravity_levels: list[str]) -> str | None:
    """Generates an explicit scientific warning if comparing across different buoyancy regimes."""
    if not gravity_levels or len(gravity_levels) < 2:
        return None

    normalized_levels = {normalize_gravity_level(g) for g in gravity_levels}
    if len(normalized_levels) <= 1:
        return None

    regimes = {classify_convection_regime(g) for g in normalized_levels}
    categories = {get_gravity_regime_category(g) for g in normalized_levels}

    return (
        f"Scientific Non-Equivalence Warning: Comparing data across disparate gravitational regimes "
        f"({', '.join(sorted(categories))}). Buoyant natural convection shifts from "
        f"{', '.join(sorted(regimes))}, invalidating direct burning rate or soot comparison without "
        f"Grashof-number and Stefan-diffusion correction scaling."
    )
