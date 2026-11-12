# Implementation Plan

## [Overview]

Implement an "Antigravity" capability for the Flame in Freefall platform that expands microgravity combustion analysis beyond the current microgravity (~10⁻⁶ g) vs normal gravity (1g) binary. The feature adds hypergravity, lunar (0.16g), and Mars (0.38g) gravity regimes, a dedicated Antigravity Comparison Workspace view, and backend API/ML support for multi-gravity condition equivalence assessment. All changes follow the existing codebase conventions: FastAPI + SQLAlchemy 2.0 backend, Next.js 15 frontend, Pydantic schemas, and strict zero-fabrication NULL preservation.

Scope covers: database schema extensions (gravity_level value expansion, new investigation records), API endpoints (gravity-filtered investigation listing, antigravity comparison), ML entity extraction (gravity regime detection), frontend views (Antigravity comparison page, gravity filter chips), and test coverage (backend unit tests, E2E tier tests).

Context: The project already supports `microgravity (~10^-6 g)` and `normal_gravity (1.0 g)` gravity levels with comparison non-equivalence detection. The antigravity feature extends this to a full gravity spectrum with a dedicated visualization workspace.

High-level approach: Extend existing models/schemas/endpoints rather than creating parallel systems; reuse the InvestigationService, ComparisonService, SI pipeline, and frontend API client patterns; add new gravity-specific data and views.

## [Types]

### New/Extended Type Definitions

**GravityLevel enum** (backend/app/core/gravity.py):
```python
class GravityLevel(str, Enum):
    MICROGRAVITY = "microgravity (~10^-6 g)"
    LUNAR = "lunar_gravity (0.16 g)"
    MARS = "mars_gravity (0.38 g)"
    NORMAL = "normal_gravity (1.0 g)"
    HYPERGRAVITY_2G = "hypergravity_2g (2.0 g)"
    HYPERGRAVITY_5G = "hypergravity_5g (5.0 g)"
```

**AntigravityCompareRequest** (backend/app/schemas/compare.py):
```python
class AntigravityCompareRequest(BaseModel):
    investigation_ids: list[str] = Field(..., min_length=2, max_length=5)
    gravity_regimes: list[str] | None = None
    include_equivalence_matrix: bool = True
```

**GravityRegimeProfile** (backend/app/schemas/compare.py):
```python
class GravityRegimeProfile(BaseModel):
    gravity_level: str
    buoyancy_parameter: float
    convection_regime: str
    flame_geometry: str
    soot_behavior: str
```

**AntigravityCompareResponse** (backend/app/schemas/compare.py):
```python
class AntigravityCompareResponse(BaseModel):
    investigation_ids: list[str]
    gravity_regimes_compared: list[str]
    equivalence_assessment: EquivalenceAssessment
    gravity_matrix: dict[str, GravityRegimeProfile]
    comparison_grid: dict[str, Any]
    buoyancy_warning: str | None
```

**Extended EquivalenceAssessment** (backend/app/schemas/compare.py): Add optional `buoyancy_warning: str | None = None`.

**Extended InvestigationSummary** (frontend/src/types/index.ts): Add optional `gravity_regime_category: string | null`.

**AntigravityComparisonResult** (frontend/src/types/index.ts): New interface matching AntigravityCompareResponse.

### Modified Types

- `Investigation.gravity_level` column: remains String(50) but now accepts expanded set of values (no DB schema change needed, application-level validation expansion).
- `ComparisonService.compare()`: extended to accept optional gravity regime filtering and return buoyancy profiles.
- `EquivalenceAssessment`: gains optional `buoyancy_warning` field.

## [Files]

### New Files

1. **`backend/app/core/gravity.py`** — Gravity regime constants, buoyancy parameter calculations, and convection regime classification.
2. **`backend/app/services/antigravity_service.py`** — AntigravityComparisonService with multi-gravity comparison logic and buoyancy warning generation.
3. **`backend/app/api/v1/endpoints/antigravity.py`** — FastAPI router with `/api/v1/antigravity/compare` POST endpoint.
4. **`frontend/src/app/antigravity/page.tsx`** — Next.js App Router page for Antigravity Comparison Workspace.
5. **`frontend/src/components/AntigravityWarning.tsx`** — Reusable buoyancy/convection warning alert component.
6. **`frontend/src/components/GravityRegimeBadge.tsx`** — Badge component displaying gravity level with convection regime color coding.
7. **`backend/tests/test_antigravity.py`** — Backend unit tests for antigravity comparison, gravity filtering, and buoyancy warnings.
8. **`tests/e2e/test_tier1_antigravity.py`** — E2E Tier 1 tests for antigravity endpoints.
9. **`tests/e2e/test_tier4_antigravity_journey.py`** — E2E Tier 4 user journey for antigravity comparison workflow.

### Existing Files to Modify

1. **`backend/app/api/v1/router.py`** — Register new antigravity router.
2. **`backend/app/schemas/compare.py`** — Add AntigravityCompareRequest, AntigravityCompareResponse, GravityRegimeProfile; extend EquivalenceAssessment with buoyancy_warning.
3. **`backend/app/services/comparison_service.py`** — Extend compare() to support gravity regime filtering and buoyancy profile generation; add gravity non-equivalence detection for expanded gravity set.
4. **`backend/app/services/investigation_service.py`** — Add gravity_level filter values to VALID_GRAVITY_LEVELS; extend list_investigations with gravity regime filtering.
5. **`backend/app/ml/entity_extractor.py`** — Add gravity regime patterns (lunar, mars, hypergravity, 1g, microgravity) to FACILITY_PATTERNS or new GRAVITY_PATTERNS.
6. **`backend/app/services/seed_data.py`** — Add new investigation records for lunar, Mars, and hypergravity gravity levels.
7. **`frontend/src/lib/api.ts`** — Add `fetchAntigravityCompare()` function; add gravity regime query params to `fetchInvestigations()`.
8. **`frontend/src/types/index.ts`** — Add AntigravityCompareResponse, GravityRegimeProfile interfaces; extend InvestigationSummary with gravity_regime_category.
9. **`frontend/src/app/compare/page.tsx`** — Add gravity regime filter options (lunar, mars, hypergravity) to comparison workspace.
10. **`frontend/src/app/investigations/page.tsx`** — Add new gravity filter options (lunar, mars, hypergravity, 2g, 5g).
11. **`frontend/src/components/Navbar.tsx`** — Add Antigravity navigation item.
12. **`PROJECT.md`** — Update endpoint contracts with antigravity endpoints and expanded gravity levels.
13. **`README.md`** — Add antigravity feature to demo script and feature list.

### Files to Delete
None.

### Files to Move
None.

### Configuration Updates
- `backend/pyproject.toml`: No new dependencies needed.
- `frontend/package.json`: No new dependencies needed.

## [Functions]

### New Functions

1. **`classify_convection_regime(gravity_level: str) -> str`** in `backend/app/core/gravity.py`
   - Returns "suppressed", "moderate", or "strong" based on gravity level.

2. **`calculate_buoyancy_parameter(gravity_level: str) -> float`** in `backend/app/core/gravity.py`
   - Returns Grashof-number-derived buoyancy indicator (0.0 to 1.0 scale).

3. **`classify_flame_geometry(gravity_level: str) -> str`** in `backend/app/core/gravity.py`
   - Returns "spherical", "teardrop", or "plume".

4. **`classify_soot_behavior(gravity_level: str) -> str`** in `backend/app/core/gravity.py`
   - Returns "trapped", "flickering", or "rising".

5. **`get_gravity_regime_category(gravity_level: str) -> str`** in `backend/app/core/gravity.py`
   - Returns "microgravity", "partial_gravity", "normal_gravity", or "hypergravity".

6. **`AntigravityComparisonService.compare_with_gravity_regimes(...)`** in `backend/app/services/antigravity_service.py`
   - Extended comparison with gravity regime profiles and buoyancy warnings.

7. **`antigravity_compare_endpoint(payload, db)`** in `backend/app/api/v1/endpoints/antigravity.py`
   - POST `/api/v1/antigravity/compare` handler.

8. **`fetchAntigravityCompare(ids, regimes?)`** in `frontend/src/lib/api.ts`
   - Calls POST `/api/v1/antigravity/compare`.

9. **`AntigravityComparisonWorkspace()`** in `frontend/src/app/antigravity/page.tsx`
   - Main page component with gravity regime selector and comparison matrix.

10. **`AntigravityWarning({regimes})`** in `frontend/src/components/AntigravityWarning.tsx`
    - Alert component showing buoyancy non-equivalence warnings.

11. **`GravityRegimeBadge({gravityLevel})`** in `frontend/src/components/GravityRegimeBadge.tsx`
    - Color-coded badge for gravity level display.

### Modified Functions

1. **`ComparisonService.compare()`** in `backend/app/services/comparison_service.py`
   - Add optional `gravity_regimes` parameter; extend equivalence assessment with buoyancy warning when gravity levels differ beyond microgravity vs 1g.

2. **`InvestigationService.list_investigations()`** in `backend/app/services/investigation_service.py`
   - Expand gravity level validation to include lunar, mars, hypergravity values.

3. **`ScientificEntityExtractor.extract_entities()`** in `backend/app/ml/entity_extractor.py`
   - Add gravity regime pattern matching for lunar, mars, 2g, 5g, microgravity, 1g.

4. **`fetchInvestigations()`** in `frontend/src/lib/api.ts`
   - Ensure new gravity values pass through query params.

5. **`compareInvestigations()`** in `frontend/src/lib/api.ts`
   - Ensure new gravity comparison endpoint is callable.

### Removed Functions
None.

## [Classes]

### New Classes

1. **`GravityRegime`** (dataclass or enum) in `backend/app/core/gravity.py`
   - Key methods: `buoyancy_parameter()`, `convection_regime()`, `flame_geometry()`, `soot_behavior()`.

2. **`AntigravityComparisonService`** in `backend/app/services/antigravity_service.py`
   - Key methods: `compare_with_gravity_regimes(session, investigation_ids, gravity_regimes)`, `generate_buoyancy_warning(records)`.

3. **`AntigravityRouter`** (APIRouter) in `backend/app/api/v1/endpoints/antigravity.py`
   - Routes: POST `/compare`.

### Modified Classes

1. **`ComparisonService`** in `backend/app/services/comparison_service.py`
   - Add gravity regime awareness to `compare()`; extend `EquivalenceAssessment` output with `buoyancy_warning`.

2. **`InvestigationService`** in `backend/app/services/investigation_service.py`
   - Expand gravity level validation set.

3. **`ScientificEntityExtractor`** in `backend/app/ml/entity_extractor.py`
   - Add `GRAVITY_PATTERNS` dict and gravity extraction logic.

### Removed Classes
None.

## [Dependencies]

### New Packages
None required — all functionality uses existing dependencies:
- `fastapi`, `sqlalchemy`, `pydantic` (backend)
- `next`, `react`, `lucide-react`, `tailwindcss` (frontend)
- `pytest`, `httpx` (testing)

### Version Changes
None.

### Integration Requirements
- Backend antigravity router registered in `backend/app/api/v1/router.py`.
- Frontend antigravity page linked from Navbar.
- Docker Compose already supports backend + frontend + PostgreSQL; no changes needed.

## [Testing]

### New Test Files

1. **`backend/tests/test_antigravity.py`**
   - Test gravity regime classification (convection, buoyancy, flame geometry, soot behavior).
   - Test antigravity comparison endpoint returns correct equivalence assessment.
   - Test buoyancy warning generation for mixed gravity regimes.
   - Test gravity regime filtering in investigation listing.
   - Test entity extraction for gravity terms (lunar, mars, hypergravity).

2. **`tests/e2e/test_tier1_antigravity.py`**
   - Test POST `/api/v1/antigravity/compare` returns 200 with valid schema.
   - Test antigravity comparison with microgravity + lunar + mars.
   - Test buoyancy warning present when gravity levels differ.

3. **`tests/e2e/test_tier4_antigravity_journey.py`**
   - Test full user journey: discover investigations → select gravity regimes → compare → view buoyancy warning → inspect detail.

### Existing Test Modifications

1. **`backend/tests/test_compare.py`** — Add test cases for gravity levels beyond microgravity vs 1g (e.g., lunar vs mars).
2. **`tests/e2e/test_tier3_cross_feature.py`** — Add cross-feature test for antigravity comparison + SI query integration.
3. **`tests/e2e/conftest.py`** — Add test payloads for lunar, Mars, and hypergravity investigations.

### Validation Strategy
- All backend tests run via `uv run pytest backend/tests -v`.
- All E2E tests run via `uv run pytest tests/e2e -v`.
- Frontend build verified via `cd frontend && npm run build`.
- Zero-fabrication rule: all new gravity data must be either authentic NASA records or clearly labeled extrapolation with NULL preservation for missing values.

## [Implementation Order]

1. **Create `backend/app/core/gravity.py`** — Gravity regime constants and classification functions (foundation for all other changes).
2. **Update `backend/app/schemas/compare.py`** — Add antigravity request/response schemas and extend EquivalenceAssessment.
3. **Update `backend/app/ml/entity_extractor.py`** — Add gravity regime pattern matching.
4. **Update `backend/app/services/investigation_service.py`** — Expand gravity level validation.
5. **Update `backend/app/services/comparison_service.py`** — Extend compare() with gravity regime support and buoyancy warnings.
6. **Create `backend/app/services/antigravity_service.py`** — Antigravity comparison service.
7. **Create `backend/app/api/v1/endpoints/antigravity.py`** — Antigravity API router.
8. **Update `backend/app/api/v1/router.py`** — Register antigravity router.
9. **Update `backend/app/services/seed_data.py`** — Add lunar, Mars, hypergravity investigation records.
10. **Update `PROJECT.md`** — Document new endpoints and gravity levels.
11. **Run backend tests** — `uv run pytest backend/tests -v` (verify no regressions).
12. **Update `frontend/src/types/index.ts`** — Add antigravity TypeScript interfaces.
13. **Update `frontend/src/lib/api.ts`** — Add fetchAntigravityCompare() function.
14. **Create `frontend/src/components/GravityRegimeBadge.tsx`** — Gravity badge component.
15. **Create `frontend/src/components/AntigravityWarning.tsx`** — Buoyancy warning component.
16. **Create `frontend/src/app/antigravity/page.tsx`** — Antigravity comparison page.
17. **Update `frontend/src/components/Navbar.tsx`** — Add Antigravity nav link.
18. **Update `frontend/src/app/investigations/page.tsx`** — Add new gravity filter options.
19. **Update `frontend/src/app/compare/page.tsx`** — Add gravity regime filter options.
20. **Run frontend build** — `cd frontend && npm run build` (verify TypeScript and linting).
21. **Create `backend/tests/test_antigravity.py`** — Backend unit tests.
22. **Create `tests/e2e/test_tier1_antigravity.py`** — E2E Tier 1 tests.
23. **Create `tests/e2e/test_tier4_antigravity_journey.py`** — E2E Tier 4 journey tests.
24. **Update `tests/e2e/conftest.py`** — Add antigravity test payloads.
25. **Update `tests/e2e/test_tier3_cross_feature.py`** — Cross-feature antigravity tests.
26. **Run full test suite** — Backend + E2E + frontend build.
27. **Update `README.md`** — Document antigravity feature in demo script.
28. **Commit all changes** — Single logical commit with clean working tree.