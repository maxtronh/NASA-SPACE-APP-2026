# TEST_READY: Flame in Freefall E2E Test Suite

## Test Infrastructure Status
- **Status**: READY
- **Total Test Cases**: 83
- **Test Results**: 83 passed, 0 failed, 0 skipped (100% pass rate)
- **Suite Execution Time**: ~1.0 second
- **Test Framework**: `pytest` + `httpx` + `fastapi.testclient` via `uv`

---

## Coverage Summary by Tier

| Tier | Focus Area | Required Threshold | Implemented Tests | Status |
|---|---|:---:|:---:|:---:|
| **Tier 1** | Primary Feature Coverage (F1 - F18) | $\ge$ 25 | **29** | ✅ PASS |
| **Tier 2** | Boundary, Corner Cases & Zero-Fabrication | $\ge$ 25 | **29** | ✅ PASS |
| **Tier 3** | Pairwise Combinatorial & Cross-Feature | $\ge$ 15 | **18** | ✅ PASS |
| **Tier 4** | Real-World Application User Journeys (S1 - S7) | $\ge$ 5 | **7** | ✅ PASS |
| **Total** | Full Independent E2E Test Suite | $\ge$ 70 | **83** | ✅ PASS |

---

## Test Directory Layout

```
c:\dev\NASA-SPACE-APP-2026\tests\
├── __init__.py
└── e2e/
    ├── __init__.py
    ├── conftest.py                   # Shared fixtures, authentic NASA payloads, HTTP client
    ├── test_tier1_feature_coverage.py # 29 opaque-box feature coverage tests
    ├── test_tier2_boundary_corner.py  # 29 boundary, adversarial & null-integrity tests
    ├── test_tier3_cross_feature.py    # 18 cross-feature & pairwise combination tests
    └── test_tier4_user_journeys.py   # 7 complex end-to-end user journey workflows
```

---

## How to Run the Test Suite

### 1. Run Complete E2E Suite (Recommended)
```bash
uv run --with pytest --with httpx --with fastapi python -m pytest tests/e2e -v
```

### 2. Run Individual Tiers
```bash
# Tier 1: Feature Coverage (29 tests)
uv run --with pytest --with httpx --with fastapi python -m pytest tests/e2e/test_tier1_feature_coverage.py -v

# Tier 2: Boundary, Corner & Adversarial Tests (29 tests)
uv run --with pytest --with httpx --with fastapi python -m pytest tests/e2e/test_tier2_boundary_corner.py -v

# Tier 3: Cross-Feature Interaction Tests (18 tests)
uv run --with pytest --with httpx --with fastapi python -m pytest tests/e2e/test_tier3_cross_feature.py -v

# Tier 4: End-to-End User Journeys (7 tests)
uv run --with pytest --with httpx --with fastapi python -m pytest tests/e2e/test_tier4_user_journeys.py -v
```

### 3. Run Against Live Backend Deployment
To execute the suite against a running local backend server or Docker container (e.g., port 8000):
```bash
$env:E2E_API_BASE_URL="http://127.0.0.1:8000"
uv run --with pytest --with httpx --with fastapi python -m pytest tests/e2e -v
```

---

## Authentic NASA Test Datasets & Provenance
All test cases use genuine NASA microgravity combustion research data sourced from NTRS and PSI:
1. **FLEX-2 (Flame Extinction Experiment 2)**:
   - ISS CIR facility: Isolated n-Heptane droplet combustion and radiative/diffusive extinction.
   - NTRS URL: `https://ntrs.nasa.gov/citations/20140011032`
   - Strict Null Integrity: `soot_volume_fraction` unmeasured -> must be `NULL`, never `0.0`.
2. **ACME (Advanced Combustion via Microgravity Experiments) - CLD Flame**:
   - ISS CIR facility: Coflow laminar diffusion flame with Methane fuel.
   - NTRS URL: `https://ntrs.nasa.gov/citations/20190001859`
   - Strict Null Integrity: `initial_droplet_diameter` -> non-applicable, must be `NULL`.
3. **BASS-II (Burning and Suppression of Solids - II)**:
   - Microgravity Science Glovebox (MSG): PMMA solid slab flame spread.
   - NTRS URL: `https://ntrs.nasa.gov/citations/20160005721`
   - Strict Null Integrity: `radiative_flux` -> uncalibrated sensor, must be `NULL`.
4. **ACME Ground Reference (1g Terrestrial)**:
   - NASA Glenn 1g Burner Rig: Normal gravity counterpart for non-equivalence testing.
   - NTRS URL: `https://ntrs.nasa.gov/citations/20190001860`

---

## Real-World Workload Scenarios (Tier 4)
- **S1 (Golden Path)**: Ingests authentic FLEX-2 record -> stores with SHA-256 provenance -> discovers in catalog -> runs natural-language SI search -> retrieves verified NASA citation -> inspects detail view -> executes side-by-side comparison -> reviews dashboard analytics.
- **S2 (Condition Non-Equivalence)**: Compares microgravity ISS experiment against 1g ground reference; validates that comparison engine issues explicit `equivalent: false` warning and flags gravity mismatch.
- **S3 (Ungrounded SI Abstention)**: Submits out-of-domain query ("What is the capital of Mars?"); validates that SI engine abstains with `abstention_flag: true`, `confidence_score < 0.30`, and zero fabricated citations.
- **S4 (Missing Measurement Integrity)**: Ingests BASS-II record with unmeasured radiative flux; verifies null preservation through database storage, detail API, comparison grid, and missing data analytics.
- **S5 (Full Service Health)**: Concurrently exercises `/health`, `/investigations`, `/compare`, `/si/query`, and `/analytics/corpus` endpoints.
- **S6 (Multi-Fuel Discovery)**: Validates cross-fuel retrieval for liquid alkane (Heptane), gaseous hydrocarbon (Methane), and solid polymer (PMMA).
- **S7 (Tamper Resilience)**: Validates that payloads with altered content or injected fake zeros in unmeasured channels are rejected with HTTP 422.
