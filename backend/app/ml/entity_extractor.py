"""Scientific entity extraction engine for NASA Microgravity Combustion Research.

Recognizes combustion regimes, fuel types, oxidizer compositions, experimental
facilities, and physical measurements from scientific literature and natural language queries.
"""

from __future__ import annotations

import re

# Domain taxonomy dictionaries: canonical key -> list of patterns / synonyms
REGIME_PATTERNS: dict[str, list[str]] = {
    "droplet_combustion": [
        r"\bdroplet\b",
        r"\bisolated droplet\b",
        r"\bdroplet burning\b",
        r"\bdroplet extinction\b",
        r"\bdroplet combustion\b",
        r"\bspherical flame\b",
        r"\bd\^?2(?:\s*law)?\b",
        r"\bd2\b",
    ],
    "laminar_diffusion": [
        r"\blaminar diffusion\b",
        r"\bdiffusion flame\b",
        r"\bcoflow\b",
        r"\bco-flow\b",
        r"\bcld\b",
        r"\bsoot formation\b",
        r"\bsoot volume fraction\b",
        r"\bflame height\b",
        r"\bgas jet\b",
    ],
    "solid_flame_spread": [
        r"\bsolid flame spread\b",
        r"\bflame spread\b",
        r"\bsolid fuel\b",
        r"\bsolid slab\b",
        r"\bpmma\b",
        r"\bpolymethylmethacrylate\b",
        r"\blow-speed flow\b",
        r"\bforced flow\b",
    ],
    "smoldering": [
        r"\bsmoldering\b",
        r"\bsmolder\b",
        r"\bporous media\b",
        r"\bmicrogravity smoldering\b",
    ],
    "premixed_flame": [
        r"\bpremixed flame\b",
        r"\bpremixed combustion\b",
        r"\bflame velocity\b",
        r"\bequivalence ratio\b",
    ],
}

FUEL_PATTERNS: dict[str, list[str]] = {
    "n-Heptane": [r"\bn-heptane\b", r"\bheptane\b", r"\bc7h16\b"],
    "Methane": [r"\bmethane\b", r"\bch4\b"],
    "PMMA": [r"\bpmma\b", r"\bpolymethylmethacrylate\b", r"\bacrylic\b"],
    "Methanol": [r"\bmethanol\b", r"\bch3oh\b"],
    "Decane": [r"\bdecane\b", r"\bn-decane\b", r"\bc10h22\b"],
}

OXIDIZER_PATTERNS: dict[str, list[str]] = {
    "Air": [r"\bair\b", r"\bstandard air\b"],
    "Oxygen": [r"\boxyg(?:en)?\b", r"\bo2\b", r"\bo2 percentage\b"],
    "Nitrogen": [r"\bnitrogen\b", r"\bn2\b"],
    "Helium": [r"\bhelium\b", r"\bhe\b"],
    "Carbon Dioxide": [r"\bcarbon dioxide\b", r"\bco2\b"],
    "Diluent": [r"\bdiluent\b", r"\bdilution\b"],
}

FACILITY_PATTERNS: dict[str, list[str]] = {
    "CIR": [
        r"\bcombustion integrated rack\b",
        r"\bcir\b",
        r"\bchamber\b",
    ],
    "Drop Tower": [
        r"\bdrop tower\b",
        r"\b2\.2 second drop tower\b",
        r"\bzero-g facility\b",
        r"\bground rig\b",
    ],
    "ISS": [
        r"\binternational space station\b",
        r"\biss\b",
        r"\bmicrogravity\b",
        r"\bfreefall\b",
        r"\b0g\b",
        r"\blow gravity\b",
    ],
    "MSG": [
        r"\bmicrogravity science glovebox\b",
        r"\bmsg\b",
    ],
    "Missions": [
        r"\bflex-2\b",
        r"\bflex\b",
        r"\bacme\b",
        r"\bbass-ii\b",
        r"\bbass\b",
    ],
}

MEASUREMENT_PATTERNS: dict[str, list[str]] = {
    "Droplet Diameter": [
        r"\binitial droplet diameter\b",
        r"\bextinction diameter\b",
        r"\bdroplet diameter\b",
        r"\bdiameter\b",
    ],
    "Burning Rate": [
        r"\bburning rate constant\b",
        r"\bburning rate\b",
        r"\bburn rate\b",
        r"\bburn duration\b",
    ],
    "Flame Velocity / Spread Rate": [
        r"\bflame spread rate\b",
        r"\bspread rate\b",
        r"\bflame velocity\b",
        r"\bspread velocity\b",
    ],
    "Pressure": [
        r"\bchamber pressure\b",
        r"\bambient pressure\b",
        r"\bpressure\b",
        r"\bpsi\b",
        r"\bkpa\b",
        r"\batm\b",
        r"\bbar\b",
    ],
    "Temperature": [
        r"\bchamber temperature\b",
        r"\bambient temperature\b",
        r"\bflame temperature\b",
        r"\btemperature\b",
        r"\bkelvin\b",
        r"\bdeg[cf]\b",
    ],
    "Soot & Radiation": [
        r"\bsoot volume fraction\b",
        r"\bsoot\b",
        r"\bradiative flux\b",
        r"\bradiant emission\b",
        r"\bheat flux\b",
    ],
    "Flow & Residence": [
        r"\bfuel flow rate\b",
        r"\bcoflow air velocity\b",
        r"\bairflow velocity\b",
        r"\bresidence time\b",
        r"\bstrain rate\b",
    ],
}

GRAVITY_PATTERNS: dict[str, list[str]] = {
    "microgravity (~10^-6 g)": [
        r"\bmicrogravity\b",
        r"\b10\^-?6\s*g\b",
        r"\bzero-g\b",
        r"\bfreefall\b",
        r"\bweightless\b",
    ],
    "lunar_gravity (0.16 g)": [
        r"\blunar gravity\b",
        r"\blunar\b",
        r"\bmoon gravity\b",
        r"\b0\.16\s*g\b",
        r"\bone-sixth g\b",
    ],
    "mars_gravity (0.38 g)": [
        r"\bmars gravity\b",
        r"\bmartian gravity\b",
        r"\b0\.38\s*g\b",
        r"\bthree-eighths g\b",
    ],
    "normal_gravity (1.0 g)": [
        r"\bnormal gravity\b",
        r"\b1\.?0?\s*g\b",
        r"\bterrestrial gravity\b",
        r"\b1-g\b",
        r"\bground test\b",
    ],
    "hypergravity_2g (2.0 g)": [
        r"\bhypergravity\b",
        r"\b2\s*g\b",
        r"\b2\.0\s*g\b",
        r"\b2g\b",
    ],
    "hypergravity_5g (5.0 g)": [
        r"\b5\s*g\b",
        r"\b5\.0\s*g\b",
        r"\b5g\b",
        r"\bcentrifuge\b",
    ],
}


class ScientificEntityExtractor:
    """Extracts domain-specific combustion entities from natural language queries and documents."""

    def __init__(self) -> None:
        self._compiled_regimes = self._compile(REGIME_PATTERNS)
        self._compiled_fuels = self._compile(FUEL_PATTERNS)
        self._compiled_oxidizers = self._compile(OXIDIZER_PATTERNS)
        self._compiled_facilities = self._compile(FACILITY_PATTERNS)
        self._compiled_measurements = self._compile(MEASUREMENT_PATTERNS)
        self._compiled_gravity = self._compile(GRAVITY_PATTERNS)

    @staticmethod
    def _compile(patterns_dict: dict[str, list[str]]) -> dict[str, list[re.Pattern]]:
        compiled: dict[str, list[re.Pattern]] = {}
        for category, patterns in patterns_dict.items():
            compiled[category] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled

    def extract_entities(self, text: str) -> dict[str, list[str]]:
        """Extracts structured categories of combustion entities from text."""
        result: dict[str, list[str]] = {
            "combustion_regimes": [],
            "fuel_types": [],
            "oxidizers": [],
            "facilities": [],
            "measurements": [],
            "gravity_regimes": [],
        }

        for cat, patterns in self._compiled_regimes.items():
            if any(p.search(text) for p in patterns):
                result["combustion_regimes"].append(cat)

        for fuel, patterns in self._compiled_fuels.items():
            if any(p.search(text) for p in patterns):
                result["fuel_types"].append(fuel)

        for ox, patterns in self._compiled_oxidizers.items():
            if any(p.search(text) for p in patterns):
                result["oxidizers"].append(ox)

        for fac, patterns in self._compiled_facilities.items():
            if any(p.search(text) for p in patterns):
                result["facilities"].append(fac)

        for meas, patterns in self._compiled_measurements.items():
            if any(p.search(text) for p in patterns):
                result["measurements"].append(meas)

        for grav, patterns in self._compiled_gravity.items():
            if any(p.search(text) for p in patterns):
                result["gravity_regimes"].append(grav)

        return result

    def extract_flat(self, text: str) -> list[str]:
        """Returns a flat list of human-readable matched entities for SI explainability."""
        extracted = self.extract_entities(text)
        flat: list[str] = []

        # Convert regime keys into human-friendly terms
        regime_names = {
            "droplet_combustion": "droplet combustion",
            "laminar_diffusion": "laminar diffusion",
            "solid_flame_spread": "solid flame spread",
            "smoldering": "smoldering",
            "premixed_flame": "premixed flame",
        }
        for r in extracted["combustion_regimes"]:
            flat.append(regime_names.get(r, r))

        flat.extend(extracted["fuel_types"])

        for m in extracted["measurements"]:
            flat.append(m.lower())

        flat.extend(extracted["facilities"])
        flat.extend(extracted["oxidizers"])
        flat.extend(extracted.get("gravity_regimes", []))

        # Check for specific key phrases directly in text to maintain high entity precision
        specific_phrases = [
            ("microgravity", "microgravity"),
            ("extinction", "extinction"),
            ("soot formation", "soot formation"),
            ("n-heptane", "n-heptane"),
            ("methane", "methane"),
            ("pmma", "PMMA"),
            ("cir", "CIR facility"),
            ("d^2", "d^2 burning law"),
        ]
        text_lower = text.lower()
        for phrase, label in specific_phrases:
            if phrase in text_lower and label not in flat:
                flat.append(label)

        # Return unique in order
        seen = set()
        deduped = []
        for item in flat:
            if item.lower() not in seen:
                seen.add(item.lower())
                deduped.append(item)
        return deduped

    def has_combustion_terms(self, text: str) -> bool:
        """Determines if the text contains any recognizable combustion domain terminology."""
        extracted = self.extract_entities(text)
        total_matches = (
            len(extracted["combustion_regimes"])
            + len(extracted["fuel_types"])
            + len(extracted["measurements"])
        )
        return total_matches > 0

    def detect_primary_regime(self, text: str) -> str | None:
        """Identifies the dominant combustion regime in the text."""
        extracted = self.extract_entities(text)
        regimes = extracted["combustion_regimes"]
        if regimes:
            return regimes[0]
        return None
