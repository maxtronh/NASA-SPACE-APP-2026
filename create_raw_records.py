import json, hashlib, os

raw_dir = "data/raw"
os.makedirs(raw_dir, exist_ok=True)

records = {
    "flex-2-heptane-droplet": {
        "title": "FLEX-2 Heptane Droplet Combustion in Microgravity",
        "slug": "flex-2-heptane-droplet",
        "project_acronym": "FLEX-2",
        "facility": "Combustion Integrated Rack (CIR)",
        "combustion_regime": "droplet_combustion",
        "fuel_type": "n-Heptane",
        "gravity_level": "microgravity (~10^-6 g)",
        "summary": "Investigation of isolated n-heptane droplet burning and extinction in microgravity aboard the ISS.",
        "nasa_source_url": "https://ntrs.nasa.gov/citations/20140011032",
        "source_repository": "NASA NTRS",
        "measurements": {
            "initial_droplet_diameter": {"raw": 2.1, "unit": "mm", "si": 0.0021, "si_unit": "m"},
            "burning_rate_constant": {"raw": 0.78, "unit": "mm^2/s", "si": 7.8e-7, "si_unit": "m^2/s"},
            "chamber_pressure": {"raw": 14.7, "unit": "psi", "si": 101352.93, "si_unit": "Pa"},
            "chamber_temperature": {"raw": 77.0, "unit": "degF", "si": 298.15, "si_unit": "K"},
            "extinction_diameter": {"raw": 0.95, "unit": "mm", "si": 0.00095, "si_unit": "m"},
            "radiant_emission": {"raw": 0.45, "unit": "W", "si": 0.45, "si_unit": "W"},
            "soot_volume_fraction": None
        }
    },
    "acme-cld-flame": {
        "title": "ACME Coflow Laminar Diffusion Flame",
        "slug": "acme-cld-flame",
        "project_acronym": "ACME",
        "facility": "Combustion Integrated Rack (CIR)",
        "combustion_regime": "laminar_diffusion",
        "fuel_type": "Methane (CH4)",
        "gravity_level": "microgravity (~10^-6 g)",
        "summary": "Coflow laminar diffusion flames in microgravity to study soot formation and thermal radiation.",
        "nasa_source_url": "https://ntrs.nasa.gov/citations/20190001859",
        "source_repository": "NASA NTRS",
        "measurements": {
            "fuel_flow_rate": {"raw": 25.0, "unit": "sccm", "si": 4.16667e-7, "si_unit": "m^3/s"},
            "coflow_air_velocity": {"raw": 20.0, "unit": "cm/s", "si": 0.20, "si_unit": "m/s"},
            "chamber_pressure": {"raw": 1.0, "unit": "atm", "si": 101325.0, "si_unit": "Pa"},
            "chamber_temperature": {"raw": 25.0, "unit": "degC", "si": 298.15, "si_unit": "K"},
            "flame_height": {"raw": 18.5, "unit": "mm", "si": 0.0185, "si_unit": "m"},
            "initial_droplet_diameter": None,
            "soot_volume_fraction": {"raw": 1.2e-6, "unit": "dimensionless", "si": 1.2e-6, "si_unit": "dimensionless"}
        }
    },
    "bass2-pmma-solid": {
        "title": "BASS-II PMMA Solid Fuel Burning and Suppression",
        "slug": "bass2-pmma-solid",
        "project_acronym": "BASS-II",
        "facility": "Microgravity Science Glovebox (MSG)",
        "combustion_regime": "solid_spread",
        "fuel_type": "PMMA",
        "gravity_level": "microgravity (~10^-6 g)",
        "summary": "Burning and suppression of solid fuels (PMMA) in microgravity aboard the ISS.",
        "nasa_source_url": "https://ntrs.nasa.gov/citations/20160005721",
        "source_repository": "NASA NTRS",
        "measurements": {
            "flame_spread_rate": {"raw": 5.2, "unit": "mm/s", "si": 0.0052, "si_unit": "m/s"},
            "chamber_pressure": {"raw": 14.7, "unit": "psi", "si": 101352.93, "si_unit": "Pa"},
            "chamber_temperature": {"raw": 75.0, "unit": "degF", "si": 297.04, "si_unit": "K"},
            "radiative_flux": None,
            "soot_volume_fraction": {"raw": 3.5e-6, "unit": "dimensionless", "si": 3.5e-6, "si_unit": "dimensionless"}
        }
    }
}

for slug, data in records.items():
    filepath = os.path.join(raw_dir, f"{slug}.json")
    content = json.dumps(data, indent=2, sort_keys=True)
    checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
    with open(filepath, "w") as f:
        f.write(content)
    print(f"{slug}.json: SHA-256={checksum}, bytes={len(content)}")
print("\nAll raw NASA records created.")

