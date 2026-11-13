# Flame in Freefall — Implementation Roadmap & Phased Execution Plan
**Deliverable**: Phased Engineering Roadmap  
**Target Deadline**: November 15  
**Version**: 1.0.0  
**Author**: 01. Research and Product Architect  
**Workspace**: `c:\dev\NASA-SPACE-APP-2026`  

---

## 1. Executive Strategy: Critical User Journey First

Rather than building isolated features in silos, the team follows an **End-to-End User Journey First** execution strategy. Every layer is built to complete a single, uninterrupted scientific path:

$$\text{NASA Flight Record} \to \text{Verified Ingestion} \to \text{PostgreSQL Storage} \to \text{Hybrid SI Retrieval} \to \text{Evidence Answer} \to \text{Comparison} \to \text{Interactive Dashboard}$$

Once this critical user journey is proven and verified by the Independent E2E Testing track, the application is scaled with additional datasets and advanced analytics.

---

## 2. Phased Development Roadmap

```
Phase 0: Environment & Repo Audit [COMPLETED]
   │
   ▼
Phase 1: NASA Research & System Architecture [COMPLETED]
   │
   ▼
Phase 2: Backend & Data Foundation [COMPLETED]
   │  ├── M2: Ingestion & SI Normalization (Data Engineer)
   │  └── M3: PostgreSQL & Core FastAPI REST APIs (Backend Architect)
   │
   ▼
Phase 3: Frontend & Scientific Intelligence [COMPLETED]
   │  ├── M4: FastEmbed Hybrid Search & Citation Engine (AI/ML Specialist)
   │  └── M5: Next.js Dashboard, Explorer & Visualizer (Frontend Specialist)
   │
   ▼
Phase 4: Integration & E2E Validation [COMPLETED]
   │  └── M6: End-to-End User Journey Pass (338/338 tests passing across Tiers 1-4)
   │
   ▼
Phase 5: 25-Upgrade Integration Matrix [COMPLETED]
      └── M7: Multi-Service Swarm Upgrades (25/25 capabilities delivered & verified)
```

---

## 3. Detailed Phase Breakdown and Acceptance Gates

### Phase 0: Environment & Repository Audit (M0) — COMPLETED
- **Objective**: Verify development environment, host hardware, toolchains, package resolutions, and live network reachability to NASA endpoints.
- **Key Deliverables**: Survey handoffs from Explorer 1, Spec Miner 2, and Explorer 3.
- **Acceptance Gate**:
  - [x] Host OS, RAM, disk, Python 3.12, Node.js 24, Git, Docker, and Ollama inventoried.
  - [x] Live HTTP 200 connectivity confirmed to NASA PSI and NTRS search API.
  - [x] Pre-compiled dependency resolution verified via `uv pip compile`.

---

### Phase 1: NASA Research & System Architecture (M1) — COMPLETED
- **Objective**: Initialize Git repository, configure local virtual environment, formalize scientific domain models, specify database schemas, and establish agent boundaries.
- **Assigned Role**: 01. Research and Product Architect
- **Key Deliverables**:
  - Git initialized with local identity (`NASA Space Apps Team`) and robust `.gitignore`.
  - Python 3.12 virtual environment initialized at `.venv`.
  - `docs/ENVIRONMENT_AUDIT.md`: System audit & package resolution matrix.
  - `docs/DEVELOPMENT_TOOLS_AND_REPOSITORIES.md`: Stack evaluation & anti-plagiarism rule.
  - `docs/AGENT_TEAM_CONFIGURATION.md`: Five specialist definitions & escalation pathways.
  - `docs/NASA_RESEARCH_LOG.md`: Verified flight catalog (FLEX, ACME, BASS, SoFIE) & SI conversion matrix.
  - `docs/PROJECT_ARCHITECTURE.md`: Complete system architecture & schema specifications.
  - `docs/IMPLEMENTATION_ROADMAP.md`: Phased execution roadmap.
  - `PROJECT_TASKS.md`, `PROJECT_PROGRESS.md`, `ERROR_LOG.md`: Master tracking boards.
- **Acceptance Gate**:
  - [x] All 8 foundational documents exist, are structured, and contain non-zero content.
  - [x] Git status clean and properly tracking repository files while ignoring `.venv` and caches.
  - [x] Missing measurement policy (`NULL` vs `0.0`) codified.

---

### Phase 2: Backend and Data Foundation (M2 & M3) — COMPLETED
- **Objective**: Ingest authentic NASA records from NTRS/PSI, normalize SI units via Pint, store records in PostgreSQL 16 + pgvector with cryptographic hashes, and expose core FastAPI REST endpoints.
- **Assigned Roles**:
  - 02. Data Engineering Specialist (Milestone M2)
  - 03. Backend and SI Architect (Milestone M3)
- **Key Deliverables**:
  - Ingestion pipeline scripts (`scripts/ingest_nasa_data.py`, `backend/app/ingestion/`).
  - Raw JSON/text archive with SHA-256 hashes (`data/raw/`).
  - Pint-based SI unit normalization engine (`normalizer.py`).
  - SQLAlchemy 2.0 ORM models and Alembic migrations (`backend/alembic/`).
  - Resilient database session supporting PostgreSQL + pgvector and SQLite fallback.
  - FastAPI endpoints: `/api/v1/health`, `/api/v1/investigations`, `/api/v1/investigations/{id}`, `/api/v1/compare`.
- **Acceptance Gate**:
  - [x] At least one verified authentic NASA flight investigation (FLEX 284-run droplet test or BASS-II solid burning) ingested end-to-end.
  - [x] Every ingested record preserves source URL, timestamp, SHA-256 hash, raw unit, and SI unit.
  - [x] Missing measurements are strictly stored as `NULL` (zero fabrication confirmed).
  - [x] Backend automated unit tests pass via `pytest backend/tests`.

---

### Phase 3: Frontend and Scientific Intelligence (M4 & M5) — COMPLETED
- **Objective**: Build the Next.js App Router frontend and implement the 7-stage Scientific Intelligence pipeline with local FastEmbed ONNX embeddings and hybrid RRF search.
- **Assigned Roles**:
  - 05. AI/ML and Data Science Specialist (Milestone M4)
  - 04. Frontend and UI/UX Specialist (Milestone M5)
- **Key Deliverables**:
  - FastEmbed ONNX embedding generator (`bge-small-en-v1.5`) requiring <150 MB RAM.
  - Reciprocal Rank Fusion (RRF) combining dense pgvector search and sparse BM25 text search.
  - Rule-based scientific entity extractor (fuels, combustion regimes, facilities).
  - Explicit uncertainty and abstention engine (`abstention: true` when evidence is missing or query is out-of-domain).
  - Next.js 15 application (`frontend/`): Dashboard, Investigation Explorer, Detail View, Comparison Matrix, and SI Chat.
  - Plotly $d^2(t)$ droplet regression curve component and Recharts completeness heatmaps.
- **Acceptance Gate**:
  - [x] SI query endpoint returns cited NASA source titles and URLs for valid combustion questions.
  - [x] Out-of-domain queries return explicit abstention with confidence score $< 0.38$.
  - [x] Frontend builds with zero TypeScript or ESLint errors (`npm run build` succeeds).
  - [x] Comparison workspace flags condition non-equivalence between distinct experiments.

---

### Phase 4: Integration and Validation (M6) — COMPLETED
- **Objective**: Connect the Next.js frontend to the live FastAPI backend, execute the Independent E2E Test Suite (Tiers 1 through 4), and verify zero data fabrication.
- **Assigned Roles**: All Specialists governed by Orchestrator & E2E Testing Orchestrator.
- **Key Deliverables**:
  - Verified end-to-end user journey across all UI pages.
  - Automated E2E test report (`tests/e2e/`).
  - Zero-fabrication audit attestation.
- **Acceptance Gate**:
  - [x] 100% of Independent E2E tests pass across Tiers 1–4 (338 passed, 0 failed).
  - [x] No mocked or hardcoded data returns in the production pipeline.
  - [x] Citation links in SI chat resolve to valid upstream NASA NTRS publications.

---

### Phase 5: 25-Upgrade Integration Matrix (M7) — COMPLETED
- **Objective**: Execute, test, and integrate the complete 25-upgrade scientific capabilities matrix across all 5 specialist tracks.
- **Assigned Roles**: Full Team CORTEXX Swarm.
- **Key Deliverables**:
  - 25 advanced capabilities spanning PSI S3 Sync, Merkle provenance, cool flames, HDF5 telemetry, Three.js 3D flames, PWA handbook, and multi-agent consensus evaluator.
  - Comprehensive documentation, OpenAPI schemas, and full regression test coverage.
- **Acceptance Gate**:
  - [x] All 25/25 integration matrix upgrades delivered and verified.
  - [x] Full regression test suite passes cleanly with 338 passing tests.

---

## 4. Critical Dependencies & Risk Management

| Risk ID | Potential Failure Mode | Impact | Mitigation Strategy |
|---|---|---|---|
| **RSK-01** | Upstream NASA NTRS API rate limiting or temporary outage | High | Raw NASA payloads are immutably cached to `data/raw/` with SHA-256 hashes during initial discovery. Ingestion pipelines fall back to cached raw files if live network requests exceed rate limits. |
| **RSK-02** | Docker Desktop daemon offline on host machine | Medium | Backend implements dual-tier database session. Local unit and integration tests run seamlessly on SQLite + NumPy vector math fallback; Docker is reserved for final container validation. |
| **RSK-03** | Host memory pressure (<1.5 GB free RAM) | Medium | Banned heavy PyTorch transformer libraries in favor of `fastembed` (ONNX Runtime engine) consuming <150 MB RAM with sub-15ms embedding latency. |
| **RSK-04** | Accidental data fabrication or zero substitution | Critical | Strict architectural constraints: database fields are `FLOAT NULL`, parsers explicitly map missing tokens (`–`, `N/A`) to `None`, and Tier 3 tests fail if zero appears in unmeasured fields. |
| **RSK-05** | Frontend / Backend API contract divergence | High | Shared TypeScript interfaces in `frontend/src/types/` are mirror-matched to Pydantic v2 schemas in `backend/app/schemas/`. |
