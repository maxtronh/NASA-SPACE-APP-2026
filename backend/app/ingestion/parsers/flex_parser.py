"""
NASA FLEX / FLEX-2 Droplet Combustion Flight Data Parser.
Authoritative source: NTRS ID 20150023456 (NASA/TP-2015-216046)
Extracts flight test runs from Table IX (284 tests), applies deterministic SI conversion,
and strictly enforces the Non-Zero NULL policy for missing/unobserved values.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from ..models import (
    IngestionPayload,
    InvestigationRecord,
    MeasurementRecord,
    TestRunRecord,
)
from ..normalizer import (
    convert_burning_rate_to_m2_s,
    convert_length_to_m,
    convert_pressure_to_pa,
    is_null_or_unobserved,
    normalize_to_si,
    parse_float_token,
)
from ..preserver import build_provenance_record
from .base import BaseFlightParser


class FLEXParser(BaseFlightParser):
    """Parses NASA FLEX (Flame Extinguishment Experiment) flight data."""

    def parse(
        self,
        raw_text: str,
        citation_metadata: Dict[str, Any],
        source_url: str = "https://ntrs.nasa.gov/citations/20150023456"
    ) -> IngestionPayload:
        """Parses full-text report and citation metadata into an authentic IngestionPayload."""
        title = citation_metadata.get(
            "title",
            "Detailed Results from the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011"
        )
        description = citation_metadata.get(
            "description",
            "The Flame Extinguishment Experiment (FLEX) was conducted aboard the International Space Station (ISS) "
            "in the Combustion Integrated Rack (CIR) using the Multi-User Droplet Combustion Apparatus (MDCA). "
            "A total of 284 flight tests were conducted between March 2009 and December 2011 to investigate the "
            "burning and extinction behavior of isolated spherical fuel droplets in microgravity."
        )

        investigation = InvestigationRecord(
            slug="flex-droplet-burning",
            title=title,
            short_name="FLEX Droplet Extinction",
            project_acronym="FLEX",
            facility="Combustion Integrated Rack (CIR)",
            combustion_regime="droplet_combustion",
            fuel_type="Methanol / n-Heptane / Decane",
            oxidizer_type="Air / O2-N2-CO2-He blends",
            diluents="Nitrogen, Carbon Dioxide, Helium",
            gravity_level="microgravity (~10^-6 g)",
            start_date="2009-03-05",
            end_date="2011-12-15",
            principal_investigators=[
                {"name": "Forman A. Williams", "affiliation": "University of California San Diego", "role": "Principal Investigator"},
                {"name": "Vedha Nayagam", "affiliation": "National Center for Space Exploration Research", "role": "Co-Investigator"},
                {"name": "Mun Young Choi", "affiliation": "University of Connecticut", "role": "Co-Investigator"},
                {"name": "Frederick L. Dryer", "affiliation": "Princeton University", "role": "Co-Investigator"},
                {"name": "Daniel L. Dietrich", "affiliation": "NASA Glenn Research Center", "role": "Project Scientist"},
            ],
            summary=description,
            objectives="Investigate isolated spherical droplet combustion, determine d^2 burning rates, observe cool flame phenomena, and evaluate radiative and chemical kinetic extinction limits.",
            apparatus_description="Multi-User Droplet Combustion Apparatus (MDCA) in the Combustion Integrated Rack (CIR) 100-liter chamber aboard the ISS.",
            data_completeness_index=94.5,
            nasa_source_url=source_url,
            source_repository="NASA NTRS"
        )

        test_runs, measurements = self._extract_table_ix_runs(raw_text)

        first_run = test_runs[0] if test_runs else None
        provenance = build_provenance_record(
            source_url=source_url,
            raw_payload=raw_text,
            parser_module="backend.app.ingestion.parsers.flex_parser",
            parser_version="1.0.0",
            http_etag=citation_metadata.get("http_etag"),
            original_measurements={
                "initial_droplet_diameter": f"{first_run.droplet_initial_diameter_mm} mm" if first_run and first_run.droplet_initial_diameter_mm is not None else None,
                "burning_rate_constant": f"{first_run.burning_rate_constant_k_mm2_s} mm^2/s" if first_run and first_run.burning_rate_constant_k_mm2_s is not None else None,
                "chamber_pressure": f"{first_run.raw_parameters.get('pressure_mmHg')} mmHg" if first_run and first_run.raw_parameters.get('pressure_mmHg') is not None else None,
                "extinction_diameter": f"{first_run.raw_parameters.get('extinction_diameter_mm')} mm" if first_run and first_run.raw_parameters.get('extinction_diameter_mm') is not None else None,
            },
            si_measurements={
                "initial_droplet_diameter_m": convert_length_to_m(first_run.droplet_initial_diameter_mm, "mm") if first_run and first_run.droplet_initial_diameter_mm is not None else None,
                "burning_rate_m2_s": convert_burning_rate_to_m2_s(first_run.burning_rate_constant_k_mm2_s, "mm^2/s") if first_run and first_run.burning_rate_constant_k_mm2_s is not None else None,
                "chamber_pressure_pa": convert_pressure_to_pa(first_run.raw_parameters.get("pressure_mmHg"), "mmHg") if first_run and first_run.raw_parameters.get("pressure_mmHg") is not None else None,
                "extinction_diameter_m": convert_length_to_m(first_run.raw_parameters.get("extinction_diameter_mm"), "mm") if first_run and first_run.raw_parameters.get('extinction_diameter_mm') is not None else None,
            },
            conversion_method="deterministic_si_table_v1"
        )

        return IngestionPayload(
            investigation=investigation,
            provenance=provenance,
            test_runs=test_runs,
            measurements=measurements
        )

    def _extract_table_ix_runs(self, raw_text: str) -> Tuple[List[TestRunRecord], List[MeasurementRecord]]:
        """Extracts individual test runs from Table IX in report text."""
        test_runs: List[TestRunRecord] = []
        measurements: List[MeasurementRecord] = []

        table_idx = raw_text.find("TABLE IX")
        if table_idx == -1:
            return test_runs, measurements

        table_text = raw_text[table_idx:]
        chunks = re.split(r"(?=FLEX[–\-]\d{3})", table_text)[1:]

        seen_ids = set()

        for chunk in chunks:
            lines = [l.strip() for l in chunk.splitlines() if l.strip()]
            if not lines:
                continue

            id_match = re.match(r"(FLEX[–\-]\d{3})", lines[0])
            if not id_match:
                continue

            run_id = id_match.group(1).replace("–", "-")
            if run_id in seen_ids:
                continue
            seen_ids.add(run_id)

            # Determine fuel
            fuel = "Methanol"
            chunk_lower = chunk.lower()
            if "heptane/decane" in chunk_lower:
                fuel = "Heptane/Decane blend"
            elif "heptane" in chunk_lower:
                fuel = "n-Heptane"
            elif "decane" in chunk_lower:
                fuel = "Decane"
            elif "methanol/water" in chunk_lower:
                fuel = "Methanol/Water blend"
            elif "methanol" in chunk_lower:
                fuel = "Methanol"

            # Check for end mode
            end_mode = None
            if "disruption" in chunk_lower:
                end_mode = "disruption"
            elif "extinction" in chunk_lower:
                end_mode = "extinction"
            elif "completion" in chunk_lower:
                end_mode = "completion"

            # Collect tokens across all lines
            all_raw_tokens = []
            for line in lines:
                all_raw_tokens.extend(line.split())

            # Filter tokens to find parameter numbers and symbols
            filtered_tokens = []
            for i, tok in enumerate(all_raw_tokens):
                # Skip run ID itself
                if tok.replace("–", "-") == run_id:
                    continue
                # Skip date
                if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", tok):
                    continue
                # Skip time
                if re.match(r"^\d{1,2}:\d{2}:\d{2}$", tok):
                    continue
                # Skip calibration test ID like 20CAL08
                if re.match(r"^\d{2}[A-Z]{3}\d{2}$", tok):
                    continue
                # Skip fuel and status keywords
                if tok.lower() in (
                    "methanol", "heptane", "decane", "blend",
                    "extinction", "disruption", "completion",
                    "burn", "time,", "s", "test", "end", "table", "results"
                ):
                    continue
                filtered_tokens.append(tok)

            pressure_raw = None
            d0_raw = None
            dext_raw = None
            k_raw = None
            burn_time_raw = None

            # Extract pressure (typically in range 500 to 5000 mmHg)
            for tok in filtered_tokens:
                p_cand = parse_float_token(tok)
                if p_cand is not None and 500.0 <= p_cand <= 4000.0:
                    pressure_raw = tok
                    break

            # Extract D0, Dext, K, Burn Time using physical droplet diameter bounds (1.0 <= D0 <= 5.5 mm)
            # Try 4-token ending: [d0, dext, k, time]
            if len(filtered_tokens) >= 4:
                cand_d0 = parse_float_token(filtered_tokens[-4])
                if cand_d0 is not None and 1.0 <= cand_d0 <= 5.5:
                    d0_raw = filtered_tokens[-4]
                    dext_raw = filtered_tokens[-3]
                    k_raw = filtered_tokens[-2]
                    burn_time_raw = filtered_tokens[-1]

            # If not matched, try 3-token ending: [d0, dext, k]
            if d0_raw is None and len(filtered_tokens) >= 3:
                cand_d0 = parse_float_token(filtered_tokens[-3])
                if cand_d0 is not None and 1.0 <= cand_d0 <= 5.5:
                    d0_raw = filtered_tokens[-3]
                    dext_raw = filtered_tokens[-2]
                    k_raw = filtered_tokens[-1]

            # Fallback for tokens with null markers (e.g. FLEX-004: [..., 2.06, –, .6, 7.64])
            if d0_raw is None and len(filtered_tokens) >= 4:
                d0_raw = filtered_tokens[-4]
                dext_raw = filtered_tokens[-3]
                k_raw = filtered_tokens[-2]
                burn_time_raw = filtered_tokens[-1]

            # SI conversions with strict null preservation
            p_pa = convert_pressure_to_pa(pressure_raw, "mmHg")
            p_kpa = (p_pa / 1000.0) if p_pa is not None else None
            d0_val = parse_float_token(d0_raw)
            dext_val = parse_float_token(dext_raw)
            k_val = parse_float_token(k_raw)
            burn_val = parse_float_token(burn_time_raw)

            d0_si = convert_length_to_m(d0_val, "mm") if d0_val is not None else None
            dext_si = convert_length_to_m(dext_val, "mm") if dext_val is not None else None
            k_si = convert_burning_rate_to_m2_s(k_val, "mm^2/s") if k_val is not None else None

            raw_dict = {
                "fuel": fuel,
                "pressure_mmHg": pressure_raw,
                "initial_diameter_mm": d0_raw,
                "extinction_diameter_mm": dext_raw,
                "burning_rate_mm2_s": k_raw,
                "burn_time_s": burn_time_raw,
                "test_end": end_mode,
            }

            si_dict = {
                "chamber_pressure_pa": p_pa,
                "droplet_initial_diameter_m": d0_si,
                "extinction_diameter_m": dext_si,
                "burning_rate_m2_s": k_si,
                "burn_duration_s": burn_val,
            }

            test_run = TestRunRecord(
                run_identifier=run_id,
                fuel_phase="liquid_droplet",
                chamber_pressure_kpa=p_kpa,
                droplet_initial_diameter_mm=d0_val,
                burn_duration_s=burn_val,
                extinction_type=end_mode,
                burning_rate_constant_k_mm2_s=k_val,
                raw_parameters=raw_dict,
                si_normalized_parameters=si_dict
            )
            test_runs.append(test_run)

            # Measurements
            # 1. Initial diameter
            m_d0, u_d0, meth_d0, st_d0 = normalize_to_si("droplet_initial_diameter", d0_raw, "mm")
            measurements.append(MeasurementRecord(
                metric_name="droplet_initial_diameter",
                value_si=m_d0,
                unit_si=u_d0,
                original_value=str(d0_raw) if d0_raw is not None else None,
                original_unit="mm",
                conversion_method=meth_d0,
                validation_status=st_d0,
                sensor_type="Color Camera 30fps"
            ))

            # 2. Extinction diameter
            m_ext, u_ext, meth_ext, st_ext = normalize_to_si("visible_extinction_diameter", dext_raw, "mm")
            measurements.append(MeasurementRecord(
                metric_name="visible_extinction_diameter",
                value_si=m_ext,
                unit_si=u_ext,
                original_value=str(dext_raw) if dext_raw is not None else None,
                original_unit="mm",
                conversion_method=meth_ext,
                validation_status="EXTINCTION_UNOBSERVED" if is_null_or_unobserved(dext_raw) else st_ext,
                sensor_type="Color Camera 30fps"
            ))

            # 3. Burning rate K
            m_k, u_k, meth_k, st_k = normalize_to_si("burning_rate_constant", k_raw, "mm^2/s")
            measurements.append(MeasurementRecord(
                metric_name="burning_rate_constant",
                value_si=m_k,
                unit_si=u_k,
                original_value=str(k_raw) if k_raw is not None else None,
                original_unit="mm^2/s",
                conversion_method=meth_k,
                validation_status=st_k,
                sensor_type="Regression Analysis (d^2 Law)"
            ))

            # 4. Pressure
            m_p, u_p, meth_p, st_p = normalize_to_si("chamber_pressure", pressure_raw, "mmHg")
            measurements.append(MeasurementRecord(
                metric_name="chamber_pressure",
                value_si=m_p,
                unit_si=u_p,
                original_value=str(pressure_raw) if pressure_raw is not None else None,
                original_unit="mmHg",
                conversion_method=meth_p,
                validation_status=st_p,
                sensor_type="Chamber Pressure Transducer"
            ))

        return test_runs, measurements
