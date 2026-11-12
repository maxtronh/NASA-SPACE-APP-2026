# Flame in Freefall — Agent Team Configuration & Specialist Matrix
**Deliverable**: R1 System & Environment Documentation  
**Version**: 1.0.0  
**Author**: 01. Research and Product Architect  
**Workspace**: `c:\dev\NASA-SPACE-APP-2026`  

---

## 1. Project Command Structure

The "Flame in Freefall" development lifecycle is organized into a coordinated Five-Specialist Agent Team governed by a centralized Project Orchestrator and validated by an Independent End-to-End (E2E) Testing Track.

```
                  ┌────────────────────────────────────────┐
                  │          Project Orchestrator          │
                  │   (Architecture, Integration, Gates)   │
                  └───────────────────┬────────────────────┘
                                      │
         ┌──────────────┬─────────────┼──────────────┬──────────────┐
         ▼              ▼             ▼              ▼              ▼
  ┌──────────────┐┌────────────┐┌────────────┐┌────────────┐┌────────────┐
  │ 01. Research ││  02. Data  ││03. Backend ││04. Frontend││05. AI/ML & │
  │  & Product   ││Engineering ││   & SI     ││  & UI/UX   ││Data Science│
  │  Architect   ││ Specialist ││ Architect  ││ Specialist ││ Specialist │
  └──────────────┘└────────────┘└────────────┘└────────────┘└────────────┘
         ▲              ▲             ▲              ▲              ▲
         └──────────────┴─────────────┼──────────────┴──────────────┘
                                      │
                  ┌───────────────────┴────────────────────┐
                  │       Independent E2E Testing Track    │
                  │  (Opaque-Box Tiers 1-4, Verification)  │
                  └────────────────────────────────────────┘
```

---

## 2. Five Specialist Agent Specifications

### 2.1 Agent 1: Research and Product Architect
- **Mission**: Establish scientific veracity, research cataloguing, system architecture, requirements compliance, and environmental auditing.
- **Key Responsibilities**:
  - Define scientific domain models (droplet combustion, flame extinction, soot dynamics, spherical flame propagation).
  - Catalogue official NASA microgravity flight investigations (FLEX, ACME, BASS, SoFIE) with verified citations.
  - Audit development environment, toolchains, package compatibility, and network reachability.
  - Maintain user-facing project tracking artifacts (`PROJECT_TASKS.md`, `PROJECT_PROGRESS.md`, `ERROR_LOG.md`).
- **Exclusive File Ownership**:
  - `docs/ENVIRONMENT_AUDIT.md`
  - `docs/DEVELOPMENT_TOOLS_AND_REPOSITORIES.md`
  - `docs/AGENT_TEAM_CONFIGURATION.md`
  - `docs/NASA_RESEARCH_LOG.md`
  - `PROJECT_TASKS.md`
  - `PROJECT_PROGRESS.md`
  - `ERROR_LOG.md`
  - `.git` initialization and `.gitignore`
- **Input Dependencies**: NASA NTRS & PSI APIs, Space Apps project requirements, Survey handoffs.
- **Output Contracts**: Audited tool configurations, verified NASA research logs, task breakdowns, roadmap governance.

---

### 2.2 Agent 2: Data Engineering Specialist
- **Mission**: Construct and execute a robust, repeatable NASA data ingestion pipeline with cryptographic provenance and SI unit normalization.
- **Key Responsibilities**:
  - Implement 7-phase ingestion pipeline: Discover, Fetch, Preserve, Parse, Normalize, Validate, Index.
  - Query NTRS REST API and extract flight experiment tables (e.g. 284 droplet tests in FLEX Table IX, BASS-II solid burning matrices).
  - Enforce cryptographic integrity: compute SHA-256 checksums, record HTTP ETags, timestamps, and raw payload paths.
  - Build Pint-based SI unit normalization engine: convert imperial/aerospace units ($mm$, $in$, $mmHg$, $atm$, $psi$, $sccm$) to SI ($m$, $Pa$, $m^3/s$).
  - **Zero Fabrication & Null Preservation**: Guarantee missing measurements are stored as `NULL` (never replaced with `0.0`).
- **Exclusive File Ownership**:
  - `backend/app/ingestion/` (or `scripts/ingest_nasa_data.py`, `scripts/normalizer.py`, `scripts/validator.py`)
  - `data/raw/` (immutable raw JSON/text files from NASA)
  - `data/processed/` (validated, normalized JSON/CSV artifacts)
  - Ingestion test suites (`backend/tests/test_ingestion.py`, `backend/tests/test_si_normalization.py`)
- **Input Dependencies**: NTRS API endpoints and scientific specifications from Agent 1.
- **Output Contracts**: Validated JSON payloads conforming to `schemas/ingestion_record.json` with dual-unit representations (`raw_value`, `raw_unit`, `si_value`, `si_unit`, `sha256_checksum`).

---

### 2.3 Agent 3: Backend and SI Architect
- **Mission**: Develop the core FastAPI backend, PostgreSQL/pgvector database layer, REST endpoints, and Docker Compose orchestration.
- **Key Responsibilities**:
  - Define SQLAlchemy 2.0 relational models: `investigations`, `test_runs`, `measurements`, `provenance_records`, and `embeddings`.
  - Implement Alembic database migrations and PostgreSQL 16 + pgvector extensions.
  - Implement resilient dual-tier database abstraction (PostgreSQL for containerized runs; SQLite fallback for local test execution).
  - Expose clean REST API endpoints:
    - `GET /api/v1/health`: Service health and database connection status.
    - `GET /api/v1/investigations`: Faceted search and filtering by regime, fuel, facility, and gravity level.
    - `GET /api/v1/investigations/{id}`: Detailed investigation profile with runs, measurements, and provenance.
    - `POST /api/v1/compare`: Multi-investigation parameter comparison with equivalence assessment.
    - `GET /api/v1/analytics/overview`: Corpus-wide completeness metrics, fuel distributions, and null-measurement counts.
  - Write multi-service `docker-compose.yml` for unified local deployment.
- **Exclusive File Ownership**:
  - `backend/app/main.py`
  - `backend/app/core/` (config, database session)
  - `backend/app/models/` (SQLAlchemy ORM models)
  - `backend/app/schemas/` (Pydantic API request/response models)
  - `backend/app/api/v1/` (FastAPI routers)
  - `backend/alembic/` (database migrations)
  - `backend/tests/` (unit and integration tests for API endpoints)
  - `docker-compose.yml` and `backend/Dockerfile`
- **Input Dependencies**: Normalized data contracts from Agent 2, AI/ML retrieval service from Agent 5.
- **Output Contracts**: Stable OpenAPI REST API conforming to `PROJECT.md` contracts, automated database migrations, passing backend test suite.

---

### 2.4 Agent 4: Frontend and UI/UX Specialist
- **Mission**: Design and implement an interactive, scientific Next.js dashboard, research explorer, comparison workspace, and data visualization suite.
- **Key Responsibilities**:
  - Build Next.js (TypeScript, App Router) frontend styled with Tailwind CSS and Lucide icons.
  - Deliver key application views:
    - **Main Research Dashboard**: High-level telemetry, investigation counts, fuel/facility distributions, data coverage matrix.
    - **NASA Investigation Explorer**: Searchable, faceted catalog with filters for combustion regime, fuel type, facility, and gravity level.
    - **Investigation Detail View**: In-depth view featuring experimental parameters, test run tables, provenance cards, and direct NASA NTRS citations.
    - **Multi-Investigation Comparison Workspace**: Side-by-side parameter grid highlighting research differences and condition equivalence flags.
    - **Evidence-Grounded SI Assistant Chat**: Chat workspace rendering responses, confidence scores, and citation cards with active links.
  - Render interactive scientific data visualizations via Plotly and Recharts:
    - Droplet burning curves ($d^2(t)$ regression lines).
    - Pressure and gas composition breakdowns.
    - Corpus completeness and missing data matrix.
  - Ensure zero build errors (`npm run build` succeeds cleanly).
- **Exclusive File Ownership**:
  - `frontend/src/app/` (pages and layouts)
  - `frontend/src/components/` (UI components, cards, tables, charts)
  - `frontend/src/lib/` (API client, utility functions)
  - `frontend/src/types/` (TypeScript interface definitions)
  - `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tailwind.config.ts`, `frontend/Dockerfile`
- **Input Dependencies**: REST API endpoints from Agent 3, SI query contracts from Agent 5.
- **Output Contracts**: Fully functional Next.js application connected to backend REST APIs, passing production TypeScript build.

---

### 2.5 Agent 5: AI/ML and Data Science Specialist
- **Mission**: Implement the evidence-first Scientific Intelligence pipeline, hybrid retrieval (BM25 + vector search), explainable relevance ranking, and uncertainty/abstention logic.
- **Key Responsibilities**:
  - Integrate `fastembed` with `BAAI/bge-small-en-v1.5` to generate dense 384-dimensional vector embeddings on CPU.
  - Implement Reciprocal Rank Fusion (RRF) combining BM25 keyword matching with vector cosine similarity.
  - Build rule-based scientific entity extractor: recognize fuel types ($CH_4, C_7H_{16}, PMMA$), facilities ($CIR, MSG$), and combustion regimes ($droplet, laminar\ diffusion, solid\ spread$).
  - Implement explicit uncertainty and abstention engine:
    - Return `abstention_flag = true` with transparent explanation when query falls outside microgravity combustion domain or evidence is absent.
    - Compute confidence scores based on top-k retrieval similarity.
  - Synthesize verifiable citations linking answers directly to indexed NASA Citation IDs and URLs.
  - Provide missing data analysis and feature correlation routines for the analytics workspace.
- **Exclusive File Ownership**:
  - `backend/app/ml/` (or `backend/app/services/si/`)
  - `backend/app/ml/embeddings.py` (FastEmbed wrapper)
  - `backend/app/ml/retriever.py` (Hybrid BM25 + Vector RRF engine)
  - `backend/app/ml/entity_extractor.py` (Domain terminology extraction)
  - `backend/app/ml/citation_engine.py` (Evidence verification and synthesis)
  - `backend/app/ml/abstention.py` (Confidence thresholding and abstention)
  - `backend/tests/test_si_pipeline.py` (Unit tests for ML and SI modules)
- **Input Dependencies**: Ingested investigation database from Agent 2 & Agent 3.
- **Output Contracts**: `POST /api/v1/si/query` service implementation returning answer, confidence, citation references, and explainability breakdown.

---

### 2.6 Independent E2E Testing Track
- **Mission**: Guarantee overall system integrity through opaque-box, requirement-driven end-to-end testing across 4 independent tiers.
- **Key Responsibilities**:
  - Author and execute `tests/e2e/` test suite independently from feature implementation code.
  - Test the complete critical user journey:
    $$\text{NASA Record} \to \text{Ingestion} \to \text{PostgreSQL} \to \text{Hybrid SI Search} \to \text{Cited Answer} \to \text{Comparison} \to \text{UI}$$
  - Enforce zero-fabrication and missing-data verification.
- **Exclusive File Ownership**:
  - `TEST_INFRA.md`
  - `TEST_READY.md`
  - `tests/e2e/` (opaque-box end-to-end test scripts)

---

## 3. Communication and Escalation Protocols

### 3.1 File-Based Coordination Protocol
All inter-agent handoffs, specifications, and reports must be delivered via structured markdown files within the agent state directories:
1. **Observation**: Direct tool outputs, exact file paths, line numbers, and API response status codes.
2. **Logic Chain**: Deductive, step-by-step reasoning linking observations to implementation decisions.
3. **Caveats**: Uninvestigated assumptions, fallback conditions, or known environmental bounds.
4. **Conclusion**: Explicit, actionable outcome.
5. **Verification Method**: Verbatim CLI commands to reproduce and independently verify the deliverable.

### 3.2 Liveness & Heartbeat Protocol
Each executing agent updates its respective `progress.md` after completing each meaningful subtask, stamping it with an updated UTC ISO-8601 timestamp (`Last visited: YYYY-MM-DDTHH:MM:SSZ`).

### 3.3 Escalation Pathways
- **Schema Mismatches**: If Agent 4 (Frontend) discovers an API schema mismatch with Agent 3 (Backend), the issue is escalated to the Project Orchestrator via `ERROR_LOG.md` to update `PROJECT.md` contracts before altering code.
- **Upstream Network Outages**: If NTRS or PSI API endpoints become unreachable or rate-limited during ingestion, Agent 2 falls back to verified cached raw payloads stored in `data/raw/` with a logged notice in `ERROR_LOG.md`.
- **Resource Constraints**: If system physical RAM drops below 500 MB, high-memory processes are terminated, and FastEmbed ONNX batch size is dialed down to 1.
