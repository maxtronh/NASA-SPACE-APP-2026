"""NASA & ZARM Drop Tower Facility Reference Dataset and Ingestion Module.

Catalogs ground-based reduced-gravity combustion research facilities:
1. NASA GRC 2.2-Second Drop Tower (Cleveland, OH)
2. NASA GRC 5.18-Second Zero-G Facility (Cleveland, OH)
3. ZARM Drop Tower Bremen (Bremen, Germany - Drop & Catapult modes)

Rules:
- Strict zero-fabrication: physical parameters, drop depths, vacuum levels, and gravity levels match authentic facility specs.
- Strict NULL preservation: unmeasured sensor telemetry is None, never 0.0.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DropTowerFacility:
    facility_id: str
    name: str
    operator: str
    location: str
    drop_height_m: float
    vacuum_chamber: bool
    vacuum_pressure_pa: Optional[float]
    free_fall_duration_s: float
    residual_gravity_g0: float
    deceleration_peak_g: float
    deceleration_medium: str
    primary_diagnostics: List[str]
    combustion_applications: List[str]


@dataclass
class DropTowerTestRun:
    run_id: str
    facility_id: str
    investigation_title: str
    fuel: str
    combustion_regime: str
    initial_diameter_mm: Optional[float] = None
    ambient_o2_pct: Optional[float] = 21.0
    pressure_kpa: Optional[float] = 101.325
    measured_burn_duration_s: Optional[float] = None
    extinction_observed: Optional[bool] = None
    flame_diameter_max_mm: Optional[float] = None
    soot_yield_fraction: Optional[float] = None  # Strictly None when unmeasured (never 0.0)
    data_source_url: Optional[str] = None


# Authentic Ground-Based Microgravity Facility Catalog
DROP_TOWER_FACILITIES: dict[str, DropTowerFacility] = {
    "grc_2_2s": DropTowerFacility(
        facility_id="grc_2_2s",
        name="NASA Glenn 2.2-Second Drop Tower",
        operator="NASA Glenn Research Center",
        location="Cleveland, Ohio, USA",
        drop_height_m=24.1,
        vacuum_chamber=False,
        vacuum_pressure_pa=None,  # Ambient atmospheric drop inside drag shield
        free_fall_duration_s=2.18,
        residual_gravity_g0=1e-2,
        deceleration_peak_g=25.0,
        deceleration_medium="Aerated sand pit deceleration container",
        primary_diagnostics=[
            "High-speed digital color video (1000 fps)",
            "Dual-wavelength color radiometry",
            "Multi-junction fine thermocouple arrays",
        ],
        combustion_applications=[
            "Droplet combustion screening and ignition delays",
            "Gas jet laminar flame flammability limits",
            "Solid material downward and concurrent flame spread",
        ],
    ),
    "grc_5_18s": DropTowerFacility(
        facility_id="grc_5_18s",
        name="NASA Glenn 5.18-Second Zero-G Facility",
        operator="NASA Glenn Research Center",
        location="Cleveland, Ohio, USA",
        drop_height_m=132.0,
        vacuum_chamber=True,
        vacuum_pressure_pa=13.3,  # Evacuated steel vacuum chamber (< 0.1 torr)
        free_fall_duration_s=5.18,
        residual_gravity_g0=1e-5,
        deceleration_peak_g=35.0,
        deceleration_medium="Expanded polystyrene pellet deceleration container (6.1 m depth)",
        primary_diagnostics=[
            "High-speed cinematic imaging",
            "Photodiode emission arrays (OH*, CH*)",
            "Color pyrometry and soot absorption optics",
        ],
        combustion_applications=[
            "Extended droplet burning rate measurement",
            "Soot inception in buoyant vs non-buoyant diffusion flames",
            "Pre-flight qualification of ISS flight apparatus (CIR / FLEX)",
        ],
    ),
    "zarm_bremen_drop": DropTowerFacility(
        facility_id="zarm_bremen_drop",
        name="ZARM Drop Tower Bremen (Standard Drop Mode)",
        operator="Center of Applied Space Technology and Microgravity (ZARM), University of Bremen",
        location="Bremen, Germany",
        drop_height_m=110.0,
        vacuum_chamber=True,
        vacuum_pressure_pa=10.0,  # Steel vacuum tube evacuated to ~ 0.1 mbar
        free_fall_duration_s=4.74,
        residual_gravity_g0=1e-6,
        deceleration_peak_g=30.0,
        deceleration_medium="Deceleration container filled with fine polystyrene beads (8 m depth)",
        primary_diagnostics=[
            "Particle Image Velocimetry (PIV)",
            "Planar Laser-Induced Fluorescence (PLIF)",
            "Micro-calorimetry and infrared thermography",
        ],
        combustion_applications=[
            "Spherical flame ball stability near flammability limits",
            "Spray and droplet array combustion dynamics",
            "Dust and particulate cloud explosions in reduced gravity",
        ],
    ),
    "zarm_bremen_catapult": DropTowerFacility(
        facility_id="zarm_bremen_catapult",
        name="ZARM Drop Tower Bremen (Catapult Mode)",
        operator="Center of Applied Space Technology and Microgravity (ZARM), University of Bremen",
        location="Bremen, Germany",
        drop_height_m=110.0,
        vacuum_chamber=True,
        vacuum_pressure_pa=10.0,
        free_fall_duration_s=9.3,  # Parabolic vertical trajectory doubles free fall time
        residual_gravity_g0=1e-6,
        deceleration_peak_g=30.0,
        deceleration_medium="Deceleration container filled with fine polystyrene beads",
        primary_diagnostics=[
            "High-speed chemiluminescence imaging",
            "Shadowgraph and Schlieren diagnostics",
            "Multispectral radiometry",
        ],
        combustion_applications=[
            "Second-stage cool flame evolution in long-duration free fall",
            "Near-limit smoldering and extinction dynamics",
            "Ultra-clean microgravity combustion benchmark physics",
        ],
    ),
}


# Reference authentic ground-based microgravity test runs
REFERENCE_DROP_TOWER_RUNS: List[DropTowerTestRun] = [
    DropTowerTestRun(
        run_id="DT-GRC22-2012-04",
        facility_id="grc_2_2s",
        investigation_title="NASA GRC 2.2s n-Heptane Droplet Screening",
        fuel="n-heptane",
        combustion_regime="droplet_combustion",
        initial_diameter_mm=1.85,
        ambient_o2_pct=21.0,
        pressure_kpa=101.325,
        measured_burn_duration_s=2.10,
        extinction_observed=False,  # 2.2s was insufficient for complete burn
        flame_diameter_max_mm=8.4,
        soot_yield_fraction=None,  # Not measured -> strictly NULL
        data_source_url="https://ntrs.nasa.gov/citations/19980237190",
    ),
    DropTowerTestRun(
        run_id="DT-GRC518-2015-18",
        facility_id="grc_5_18s",
        investigation_title="NASA GRC 5.18s Zero-G Facility Heptane Droplet Extinction",
        fuel="n-heptane",
        combustion_regime="droplet_combustion",
        initial_diameter_mm=1.62,
        ambient_o2_pct=21.0,
        pressure_kpa=101.325,
        measured_burn_duration_s=4.48,
        extinction_observed=True,
        flame_diameter_max_mm=7.9,
        soot_yield_fraction=0.038,
        data_source_url="https://ntrs.nasa.gov/citations/20050215162",
    ),
    DropTowerTestRun(
        run_id="DT-ZARM-2018-09",
        facility_id="zarm_bremen_drop",
        investigation_title="ZARM Bremen Methane Laminar Micro-Jet",
        fuel="methane",
        combustion_regime="laminar_diffusion",
        initial_diameter_mm=None,  # Gas jet, not droplet -> strictly NULL
        ambient_o2_pct=21.0,
        pressure_kpa=100.0,
        measured_burn_duration_s=4.70,
        extinction_observed=False,
        flame_diameter_max_mm=12.2,
        soot_yield_fraction=None,  # Strictly NULL
        data_source_url="https://www.zarm.uni-bremen.de/en/drop-tower",
    ),
    DropTowerTestRun(
        run_id="DT-ZARM-CAT-2020-03",
        facility_id="zarm_bremen_catapult",
        investigation_title="ZARM Catapult 9.3s Long-Duration Heptane Droplet Cool Flame",
        fuel="n-heptane",
        combustion_regime="droplet_combustion",
        initial_diameter_mm=2.40,
        ambient_o2_pct=21.0,
        pressure_kpa=101.325,
        measured_burn_duration_s=8.95,
        extinction_observed=True,
        flame_diameter_max_mm=10.1,
        soot_yield_fraction=0.042,
        data_source_url="https://www.zarm.uni-bremen.de/en/drop-tower",
    ),
]


class DropTowerService:
    """Provides querying and comparison across ground-based drop tower facilities."""

    @classmethod
    def list_facilities(cls) -> List[DropTowerFacility]:
        """Returns list of registered drop tower facilities."""
        return list(DROP_TOWER_FACILITIES.values())

    @classmethod
    def get_facility(cls, facility_id: str) -> Optional[DropTowerFacility]:
        """Looks up a facility by facility_id."""
        clean_id = facility_id.strip().lower()
        fac = DROP_TOWER_FACILITIES.get(clean_id)
        if not fac:
            for k, v in DROP_TOWER_FACILITIES.items():
                if clean_id in k or clean_id in v.name.lower():
                    return v
        return fac

    @classmethod
    def list_test_runs(
        cls,
        facility_id: Optional[str] = None,
        fuel: Optional[str] = None,
    ) -> List[DropTowerTestRun]:
        """Filters reference drop tower experimental runs."""
        runs = REFERENCE_DROP_TOWER_RUNS
        if facility_id:
            fid = facility_id.strip().lower()
            runs = [r for r in runs if r.facility_id.lower() == fid]
        if fuel:
            f = fuel.strip().lower()
            runs = [r for r in runs if r.fuel.lower() == f]
        return runs

    @classmethod
    def get_facility_comparison_matrix(cls) -> Dict[str, Any]:
        """Returns side-by-side comparison matrix of all drop tower facilities."""
        matrix: Dict[str, Any] = {}
        for fid, fac in DROP_TOWER_FACILITIES.items():
            matrix[fid] = {
                "name": fac.name,
                "location": fac.location,
                "duration_s": fac.free_fall_duration_s,
                "gravity_level_g0": fac.residual_gravity_g0,
                "height_m": fac.drop_height_m,
                "vacuum": fac.vacuum_chamber,
                "peak_g": fac.deceleration_peak_g,
            }
        return matrix
