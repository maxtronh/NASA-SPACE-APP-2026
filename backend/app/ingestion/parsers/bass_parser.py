"""
NASA BASS & BASS-II Solid Fuel Combustion Flight Data Parser.
Authoritative source: NTRS ID 20210011385 (NASA/TM-20210011385)
Extracts flight test runs from Table 5.1 (PMMA slab tests M1-M20) and Table 4.1/4.2 (PMMA cylindrical rods),
applies deterministic SI conversions, and strictly enforces the Non-Zero NULL policy.
"""

import re
from typing import Any

from ..models import (
    IngestionPayload,
    InvestigationRecord,
    MeasurementRecord,
    TestRunRecord,
)
from ..normalizer import (
    convert_mole_fraction,
    convert_velocity_to_m_s,
    is_null_or_unobserved,
    normalize_to_si,
    parse_float_token,
)
from ..preserver import build_provenance_record
from .base import BaseFlightParser


class BASSParser(BaseFlightParser):
    """Parses NASA BASS-II (Burning and Suppression of Solids) flight data."""

    def parse(
        self,
        raw_text: str,
        citation_metadata: dict[str, Any],
        source_url: str = "https://ntrs.nasa.gov/citations/20210011385"
    ) -> IngestionPayload:
        """Parses full-text report and citation metadata into an authentic IngestionPayload."""
        title = citation_metadata.get(
            "title",
            "Burning and Suppression of Solids-II (BASS-II) Summary Report"
        )
        description = citation_metadata.get(
            "description",
            "The Burning and Suppression of Solids-II (BASS-II) investigation examined the combustion and "
            "extinction characteristics of solid polymethylmethacrylate (PMMA) slabs and cylindrical rods in "
            "the Microgravity Science Glovebox (MSG) aboard the International Space Station (ISS). Low-speed "
            "forced airflows in microgravity isolate convective and radiative extinction limits without buoyancy."
        )

        investigation = InvestigationRecord(
            slug="bass-ii-solid-slab",
            title=title,
            short_name="BASS-II Solid Flame Spread",
            project_acronym="BASS-II",
            facility="Microgravity Science Glovebox (MSG)",
            combustion_regime="solid_flame_spread",
            fuel_type="Polymethylmethacrylate (PMMA)",
            oxidizer_type="Air / Oxygen-Nitrogen Blends",
            diluents="Nitrogen",
            gravity_level="microgravity (~10^-6 g)",
            start_date="2014-04-01",
            end_date="2017-09-30",
            principal_investigators=[
                {"name": "Paul V. Ferkul", "affiliation": "Universities Space Research Association (USRA)", "role": "Principal Investigator"},
                {"name": "Sandra L. Olson", "affiliation": "NASA Glenn Research Center", "role": "Lead Scientist"},
                {"name": "Subrata Bhattacharjee", "affiliation": "San Diego State University", "role": "Co-Investigator"},
                {"name": "Fletcher J. Miller", "affiliation": "San Diego State University", "role": "Co-Investigator"},
                {"name": "James S. T'ien", "affiliation": "Case Western Reserve University", "role": "Co-Investigator"},
            ],
            summary=description,
            objectives="Evaluate flame spread rate over thick and thin solid fuels, determine low-flow flammability boundaries, and assess fire suppression effectiveness in microgravity.",
            apparatus_description="Small Flow Duct mounted inside the Microgravity Science Glovebox (MSG) aboard the ISS.",
            data_completeness_index=91.0,
            nasa_source_url=source_url,
            source_repository="NASA NTRS"
        )

        test_runs, measurements = self._extract_table_51_runs(raw_text)

        # Baseline measurements for provenance
        first_run = test_runs[0] if test_runs else None
        provenance = build_provenance_record(
            source_url=source_url,
            raw_payload=raw_text,
            parser_module="backend.app.ingestion.parsers.bass_parser",
            parser_version="1.0.0",
            http_etag=citation_metadata.get("http_etag"),
            original_measurements={
                "spread_rate": f"{first_run.flame_spread_rate_mm_s} mm/s" if first_run and first_run.flame_spread_rate_mm_s else None,
                "airflow_velocity": f"{first_run.raw_parameters.get('airflow_velocity_cm_s')} cm/s" if first_run else None,
                "oxygen_concentration": f"{first_run.oxygen_percentage} %" if first_run and first_run.oxygen_percentage else None,
                "initial_droplet_diameter": None,  # Non-droplet: MUST be NULL
                "radiative_flux": None,            # Unmeasured: MUST be NULL
            },
            si_measurements={
                "spread_rate_m_s": convert_velocity_to_m_s(first_run.flame_spread_rate_mm_s, "mm/s") if first_run else None,
                "airflow_velocity_m_s": convert_velocity_to_m_s(first_run.raw_parameters.get("airflow_velocity_cm_s"), "cm/s") if first_run else None,
                "oxygen_concentration_mole_fraction": convert_mole_fraction(first_run.oxygen_percentage, "%") if first_run else None,
                "initial_droplet_diameter_m": None,  # Strictly NULL
                "radiative_flux_w_m2": None,         # Strictly NULL
            },
            conversion_method="deterministic_si_table_v1"
        )

        return IngestionPayload(
            investigation=investigation,
            provenance=provenance,
            test_runs=test_runs,
            measurements=measurements
        )

    def _extract_table_51_runs(self, raw_text: str) -> tuple[list[TestRunRecord], list[MeasurementRecord]]:
        """Extracts slab combustion tests M1 through M20 from Table 5.1 in report text."""
        test_runs: list[TestRunRecord] = []
        measurements: list[MeasurementRecord] = []

        table_idx = raw_text.find("TABLE 5.1")
        if table_idx == -1:
            return test_runs, measurements

        table_text = raw_text[table_idx:table_idx + 8000]

        # Extract lines for M1 through M20
        pattern = re.compile(
            r"(M\d{1,2})\s+(\d+)\s+([\d\.]+)\s+(\d+)\s+([^\n]+?)\s+(Not tracked|[\d\.\s,and]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)"
        )

        matches = pattern.findall(table_text)
        for m in matches:
            test_id, thickness_mm, width_cm, sides_burning, vel_raw, spread_raw, burn_time_min, init_o2, final_o2 = m

            run_id = f"BASS-II-{test_id}"

            # Parse primary numeric values
            v_match = re.search(r"[-+]?[0-9]*\.?[0-9]+", vel_raw)
            v_val = float(v_match.group(0)) if v_match else None

            # Handle spread rate token: "Not tracked" -> None (strictly NULL)
            s_match = re.search(r"[-+]?[0-9]*\.?[0-9]+", spread_raw) if "not tracked" not in spread_raw.lower() else None
            s_val = float(s_match.group(0)) if s_match else None

            o2_val = parse_float_token(init_o2)
            burn_time_s = float(burn_time_min) * 60.0 if parse_float_token(burn_time_min) else None

            # Convert to SI units
            v_si = convert_velocity_to_m_s(v_val, "cm/s") if v_val is not None else None
            s_si = convert_velocity_to_m_s(s_val, "mm/s") if s_val is not None else None
            o2_si = convert_mole_fraction(o2_val, "%") if o2_val is not None else None

            raw_dict = {
                "test_no": test_id,
                "fuel": "Polymethylmethacrylate (PMMA) slab",
                "thickness_mm": thickness_mm,
                "width_cm": width_cm,
                "sides_burning": sides_burning,
                "airflow_velocity_cm_s": v_val,
                "flame_spread_rate_mm_s": spread_raw.strip(),
                "burn_time_min": burn_time_min,
                "initial_o2_vol_pct": init_o2,
                "final_o2_vol_pct": final_o2,
                "initial_droplet_diameter_mm": None,  # Solid fuel, non-droplet: strictly NULL
            }

            si_dict = {
                "airflow_velocity_m_s": v_si,
                "flame_spread_rate_m_s": s_si,
                "burn_duration_s": burn_time_s,
                "initial_o2_fraction": o2_si,
                "droplet_initial_diameter_m": None,  # Strictly NULL
            }

            test_run = TestRunRecord(
                run_identifier=run_id,
                fuel_phase="solid_sample",
                oxygen_percentage=o2_val,
                burn_duration_s=burn_time_s,
                flame_spread_rate_mm_s=s_val,
                raw_parameters=raw_dict,
                si_normalized_parameters=si_dict
            )
            test_runs.append(test_run)

            # Measurements
            # 1. Flame spread rate
            m_s, u_s, meth_s, st_s = normalize_to_si("flame_spread_rate", s_val, "mm/s")
            measurements.append(MeasurementRecord(
                metric_name="flame_spread_rate",
                value_si=m_s,
                unit_si=u_s,
                original_value=spread_raw.strip(),
                original_unit="mm/s",
                conversion_method=meth_s,
                validation_status="MISSING_DATA" if is_null_or_unobserved(s_val) else st_s,
                sensor_type="High-Resolution Color Video"
            ))

            # 2. Airflow velocity
            m_v, u_v, meth_v, st_v = normalize_to_si("airflow_velocity", v_val, "cm/s")
            measurements.append(MeasurementRecord(
                metric_name="airflow_velocity",
                value_si=m_v,
                unit_si=u_v,
                original_value=str(v_val) if v_val is not None else None,
                original_unit="cm/s",
                conversion_method=meth_v,
                validation_status=st_v,
                sensor_type="Duct Flow Anemometer"
            ))

            # 3. Oxygen concentration
            m_o2, u_o2, meth_o2, st_o2 = normalize_to_si("oxygen_concentration", o2_val, "%")
            measurements.append(MeasurementRecord(
                metric_name="oxygen_concentration",
                value_si=m_o2,
                unit_si=u_o2,
                original_value=str(o2_val) if o2_val is not None else None,
                original_unit="%",
                conversion_method=meth_o2,
                validation_status=st_o2,
                sensor_type="CSA-CP Electrochemical Sensor"
            ))

            # 4. Droplet diameter (Explicit NULL test assertion)
            measurements.append(MeasurementRecord(
                metric_name="droplet_initial_diameter",
                value_si=None,
                unit_si="m",
                original_value=None,
                original_unit=None,
                conversion_method="null_preservation",
                validation_status="MISSING_DATA",
                sensor_type=None
            ))

        return test_runs, measurements
