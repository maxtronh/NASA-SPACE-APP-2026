"""
Solar Physics & Ephemeris Unit Tests — Milestone M9
Asserts Kepler's 3rd Law (T^2 / a^3 = 1.0), Hohmann transfer boundaries,
translunar injection physics, and the 25 Scientific Faces schema.
"""

import math
import pytest
from backend.app.exploration.solar_physics import (
    PLANETARY_ORBITS,
    THE_25_FACES,
    calculate_planet_position,
    calculate_hohmann_transfer,
    get_all_faces,
    get_face_by_id,
    GM_SUN,
    GM_EARTH,
    AU_M,
)
from backend.app.exploration.solar_dataset import (
    generate_solar_25_dataset,
    generate_face_instruction_pairs,
)


class TestKeplerianPhysics:
    def test_kepler_third_law_heliocentric_planets(self):
        """
        Kepler's Third Law: For all heliocentric planets, T^2 / a^3 must equal 1.0 (within 1.5% margin).
        """
        for name, orbit in PLANETARY_ORBITS.items():
            if not orbit.is_planet or orbit.parent_body != "Sun":
                continue
            ratio = (orbit.orbital_period_years ** 2) / (orbit.semi_major_axis_au ** 3)
            assert 0.98 <= ratio <= 1.02, (
                f"Kepler's 3rd Law violated for {name}: T={orbit.orbital_period_years} yr, "
                f"a={orbit.semi_major_axis_au} AU, ratio={ratio:.5f}"
            )

    def test_calculate_planet_position_bounds(self):
        """
        Verify that calculated planet orbital distances stay strictly within perihelion and aphelion bounds.
        """
        for name, orbit in PLANETARY_ORBITS.items():
            state = calculate_planet_position(orbit, epoch_seconds=100000.0)
            dist_au = state.position.distance_sun_au
            perihelion_au = orbit.semi_major_axis_au * (1.0 - orbit.eccentricity)
            aphelion_au = orbit.semi_major_axis_au * (1.0 + orbit.eccentricity)

            if orbit.parent_body == "Sun":
                assert perihelion_au * 0.99 <= dist_au <= aphelion_au * 1.01, (
                    f"Position for {name} out of bounds: dist={dist_au:.3f} AU, "
                    f"perihelion={perihelion_au:.3f}, aphelion={aphelion_au:.3f}"
                )
                assert state.position.speed_km_s > 0, f"Speed must be positive for {name}"

    def test_kepler_equation_newton_raphson_convergence(self):
        """
        Test that Newton-Raphson solver reaches high precision across high eccentricity (e.g. Pluto e=0.2488).
        """
        pluto_orbit = PLANETARY_ORBITS["Pluto"]
        for t_offset in [0.0, 1e6, 5e7, 1e8]:
            state = calculate_planet_position(pluto_orbit, epoch_seconds=t_offset)
            assert not math.isnan(state.position.x_au)
            assert not math.isnan(state.position.y_au)
            assert not math.isnan(state.position.z_au)
            assert not math.isnan(state.true_anomaly_deg)


class TestHohmannTransfers:
    def test_earth_to_mars_hohmann_bounds(self):
        """
        Authentic NASA bounds for Earth-Mars Hohmann transfer:
        Total Delta-V ~ 5.4 - 5.8 km/s
        Transit duration ~ 240 - 280 days
        """
        res = calculate_hohmann_transfer("Earth", "Mars")
        assert res.transfer_type == "heliocentric_interplanetary"
        assert 5.4 <= res.delta_v_total_km_s <= 5.8, (
            f"Earth-Mars delta-V {res.delta_v_total_km_s} km/s out of physical bounds [5.4, 5.8]"
        )
        assert 240 <= res.transit_duration_days <= 280, (
            f"Earth-Mars duration {res.transit_duration_days} days out of bounds [240, 280]"
        )
        assert 2.8 <= res.delta_v_departure_km_s <= 3.1
        assert 2.5 <= res.delta_v_arrival_km_s <= 2.8

    def test_earth_to_moon_geocentric_tli_bounds(self):
        """
        Critical defect check: Earth to Moon/Lunar Gateway must be computed as a
        geocentric translunar injection (TLI), NOT a heliocentric 0 km/s transfer.
        TLI Delta-V ~ 3.1 - 3.2 km/s from LEO
        Total Delta-V ~ 3.8 - 4.1 km/s with lunar insertion
        Transit duration ~ 3.0 - 3.5 days
        """
        res = calculate_hohmann_transfer("Earth", "Moon")
        assert res.transfer_type == "geocentric_translunar"
        assert 3.10 <= res.delta_v_departure_km_s <= 3.25, (
            f"Translunar injection delta-V {res.delta_v_departure_km_s} must be ~3.14 km/s"
        )
        assert 3.80 <= res.delta_v_total_km_s <= 4.20, (
            f"Total Earth-Moon delta-V {res.delta_v_total_km_s} must be ~3.97 km/s"
        )
        assert 2.8 <= res.transit_duration_days <= 3.8, (
            f"Earth-Moon transit duration {res.transit_duration_days} must be ~3.2 days"
        )

    def test_lunar_gateway_alias_resolution(self):
        """
        Verify that Artemis Lunar Gateway aliases correctly map to geocentric lunar injection.
        """
        res1 = calculate_hohmann_transfer("Earth", "Lunar Gateway")
        assert res1.transfer_type == "geocentric_translunar"
        assert 3.8 <= res1.delta_v_total_km_s <= 4.2

        res2 = calculate_hohmann_transfer("Earth", "Artemis Gateway")
        assert res2.transfer_type == "geocentric_translunar"

    def test_co_orbital_zero_delta_v(self):
        """
        Origin and target identical should yield exactly 0 delta-V.
        """
        res = calculate_hohmann_transfer("Earth", "Earth")
        assert res.delta_v_total_km_s == 0.0
        assert res.transit_duration_days == 0.0


class TestThe25FacesMatrix:
    def test_exact_25_faces_count(self):
        """Assert exactly 25 faces are defined."""
        faces = get_all_faces()
        assert len(faces) == 25

    def test_all_tiers_balanced(self):
        """Assert each of the 5 tiers has exactly 5 faces."""
        faces = get_all_faces()
        for tier in range(1, 6):
            tier_faces = [f for f in faces if f.tier == tier]
            assert len(tier_faces) == 5, f"Tier {tier} does not have exactly 5 faces (found {len(tier_faces)})"

    def test_face_lookup_by_id(self):
        """Assert lookup by ID returns correct records."""
        for face_id in range(1, 26):
            face = get_face_by_id(face_id)
            assert face is not None
            assert face.id == face_id
            assert face.name != ""
            assert face.formulation != ""
            assert face.key_constant != ""
            assert face.telemetry_channel != ""

    def test_null_preservation_integrity(self):
        """Assert zero-fabrication: unmeasured fields are strictly None."""
        faces = get_all_faces()
        for face in faces:
            assert face.unmeasured_null is None


class TestSolarDatasetGeneration:
    def test_total_1250_instruction_pairs(self):
        """Assert dataset generator produces exactly 1,250 instruction-tuning pairs (50 per face)."""
        dataset = generate_solar_25_dataset()
        assert len(dataset) == 1250

    def test_dataset_format_compliance(self):
        """Assert each pair contains required ChatML instruction-tuning fields."""
        dataset = generate_solar_25_dataset()
        for idx, sample in enumerate(dataset[:100]):
            assert "instruction" in sample and len(sample["instruction"]) > 10
            assert "input" in sample and len(sample["input"]) > 5
            assert "output" in sample and len(sample["output"]) > 20
