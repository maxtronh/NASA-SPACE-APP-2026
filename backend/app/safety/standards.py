"""NASA-STD-6001B Materials Flammability Requirements and Test Standards Specification.

Covers:
- Test 1: Upward Flame Propagation (burn length < 15.2 cm / 6 inches, zero flaming drips)
- Test 7: Heat and Visible Smoke Release Rates (Peak HRR < 100 kW/m², Total HR < 20 MJ/m²)
- Spacecraft Cabin Exploration Atmospheres (ISS, Artemis Gateway, Lunar Habitat, EVA)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CabinAtmosphere:
    name: str
    code: str
    oxygen_percentage: float  # vol %
    pressure_kpa: float       # kPa
    description: str


CABIN_ATMOSPHERES: dict[str, CabinAtmosphere] = {
    "iss_standard": CabinAtmosphere(
        name="ISS Standard Cabin Atmosphere",
        code="iss_standard",
        oxygen_percentage=21.0,
        pressure_kpa=101.325,
        description="Standard sea-level terrestrial equivalent atmosphere on the ISS.",
    ),
    "artemis_gateway": CabinAtmosphere(
        name="Artemis / Gateway Exploration Atmosphere",
        code="artemis_gateway",
        oxygen_percentage=34.0,
        pressure_kpa=56.5,
        description="Low-pressure elevated-oxygen exploration atmosphere designed to reduce EVA pre-breathe times.",
    ),
    "lunar_habitat": CabinAtmosphere(
        name="Lunar Surface Habitat Atmosphere",
        code="lunar_habitat",
        oxygen_percentage=30.0,
        pressure_kpa=70.3,
        description="Intermediate exploration atmosphere for Artemis base camp lunar surface modules.",
    ),
    "eva_prebreathe": CabinAtmosphere(
        name="EVA Suit Pre-Breathe Protocol",
        code="eva_prebreathe",
        oxygen_percentage=32.0,
        pressure_kpa=55.2,
        description="Hypobaric hyperoxic pre-breathe protocol for decompression sickness prevention.",
    ),
}


@dataclass(frozen=True)
class MaterialFlammabilityProfile:
    name: str
    chemical_formula: str
    limiting_oxygen_index: float  # LOI / MOC in %
    heat_of_combustion_mj_kg: float
    char_forming: bool
    dripping_propensity: str     # "none", "low", "high"
    typical_uses: str


SPACECRAFT_MATERIALS: dict[str, MaterialFlammabilityProfile] = {
    "pmma": MaterialFlammabilityProfile(
        name="Polymethylmethacrylate (PMMA / Acrylic)",
        chemical_formula="(C5O2H8)n",
        limiting_oxygen_index=17.5,
        heat_of_combustion_mj_kg=26.2,
        char_forming=False,
        dripping_propensity="high",
        typical_uses="Window viewports, optical instruments, glovebox partitions (BASS-II flight fuel).",
    ),
    "nomex": MaterialFlammabilityProfile(
        name="Nomex (Aramid)",
        chemical_formula="(C14H10N2O2)n",
        limiting_oxygen_index=29.0,
        heat_of_combustion_mj_kg=29.8,
        char_forming=True,
        dripping_propensity="none",
        typical_uses="Crew flight suits, thermal blankets, cargo containment bags.",
    ),
    "delrin": MaterialFlammabilityProfile(
        name="Polyoxymethylene (Delrin / POM)",
        chemical_formula="(CH2O)n",
        limiting_oxygen_index=15.0,
        heat_of_combustion_mj_kg=16.8,
        char_forming=False,
        dripping_propensity="high",
        typical_uses="Structural gears, electrical insulation, mechanical bearings.",
    ),
    "polycarbonate": MaterialFlammabilityProfile(
        name="Polycarbonate (Lexan)",
        chemical_formula="(C16H14O3)n",
        limiting_oxygen_index=26.0,
        heat_of_combustion_mj_kg=30.8,
        char_forming=True,
        dripping_propensity="low",
        typical_uses="Helmet visors, impact-resistant face shields, instrument enclosures.",
    ),
    "teflon": MaterialFlammabilityProfile(
        name="Polytetrafluoroethylene (Teflon / PTFE)",
        chemical_formula="(C2F4)n",
        limiting_oxygen_index=95.0,
        heat_of_combustion_mj_kg=5.0,
        char_forming=False,
        dripping_propensity="none",
        typical_uses="High-voltage wire insulation, fluid tubing, cryogenic seals.",
    ),
    "kevlar": MaterialFlammabilityProfile(
        name="Kevlar (Para-Aramid)",
        chemical_formula="(C14H10N2O2)n",
        limiting_oxygen_index=29.5,
        heat_of_combustion_mj_kg=33.5,
        char_forming=True,
        dripping_propensity="none",
        typical_uses="Micrometeoroid shielding, structural composite wraps, tether lines.",
    ),
}
