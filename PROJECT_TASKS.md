# Flame in Freefall — Master Project Task Breakdown
**Project**: CORTEXX Scientific Intelligence Platform ("Flame in Freefall")  
**Target Deadline**: November 15  
**Governing Strategy**: End-to-End User Journey First  
$$\text{NASA Record} \to \text{Verified DB} \to \text{SI Search} \to \text{Evidence Answer} \to \text{Comparison} \to \text{Interactive Dashboard}$$

---

## 1. Priority Legend
- **P0 (Mandatory)**: Essential for working end-to-end platform, verified ingestion, and demonstration.
- **P1 (Important)**: Scientific analytics, deep faceted filtering, and explainability features.
- **P2 (Enhancement)**: Advanced predictive machine learning and extended corpus scraping.

---

## 2. Master Task Matrix

| Task ID | Specialist Role | Priority | Milestone | Task Description | Deliverable Artifacts | Dependencies | Status |
|---|---|---|---|---|---|---|---|
| **TSK-M0-01** | Orchestrator & Explorers | P0 | M0 | Workspace audit, tool discovery, and survey handoffs | Explorer & Spec Miner handoffs | None | **COMPLETED** |
| **TSK-M1-01** | 01. Research Architect | P0 | M1 | Git repository initialization, local user config, `.gitignore` | `.git`, `.gitignore` | None | **COMPLETED** |
| **TSK-M1-02** | 01. Research Architect | P0 | M1 | Python 3.12 virtual environment creation via `uv` | `.venv` | TSK-M1-01 | **COMPLETED** |
| **TSK-M1-03** | 01. Research Architect | P0 | M1 | Comprehensive Environment & System Audit | `docs/ENVIRONMENT_AUDIT.md` | TSK-M0-01 | **COMPLETED** |
| **TSK-M1-04** | 01. Research Architect | P0 | M1 | Toolstack, open-source repositories & MCP specs | `docs/DEVELOPMENT_TOOLS_AND_REPOSITORIES.md` | TSK-M0-01 | **COMPLETED** |
| **TSK-M1-05** | 01. Research Architect | P0 | M1 | Five specialist agent roles & interface boundaries | `docs/AGENT_TEAM_CONFIGURATION.md` | TSK-M0-01 | **COMPLETED** |
| **TSK-M1-06** | 01. Research Architect | P0 | M1 | NASA microgravity combustion research log & SI spec | `docs/NASA_RESEARCH_LOG.md` | TSK-M0-01 | **COMPLETED** |
| **TSK-M1-07** | 01. Research Architect | P0 | M1 | Complete system architecture & schema specifications | `docs/PROJECT_ARCHITECTURE.md` | TSK-M0-01 | **COMPLETED** |
| **TSK-M1-08** | 01. Research Architect | P0 | M1 | Phased implementation roadmap & critical user journey | `docs/IMPLEMENTATION_ROADMAP.md` | TSK-M0-01 | **COMPLETED** |
| **TSK-M1-09** | 01. Research Architect | P0 | M1 | Master tracking, progress, and error logging files | `PROJECT_TASKS.md`, `PROJECT_PROGRESS.md`, `ERROR_LOG.md` | None | **COMPLETED** |
| **TSK-E2E-01** | E2E Testing Orchestrator | P0 | M-E2E | Independent opaque-box test infrastructure definition | `TEST_INFRA.md`, `TEST_READY.md` | TSK-M0-01 | **READY** |
| **TSK-E2E-02** | E2E Testing Orchestrator | P0 | M-E2E | Automated E2E test suites (Tiers 1 to 4) | `tests/e2e/test_tier*.py` | TSK-E2E-01 | **READY** |
| **TSK-M2-01** | 02. Data Engineer | P0 | M2 | NTRS & PSI live fetching engine with rate limits | `backend/app/ingestion/fetcher.py` | TSK-M1-06 | **PENDING** |
| **TSK-M2-02** | 02. Data Engineer | P0 | M2 | Raw data preservation & cryptographic SHA-256 provenance | `backend/app/ingestion/preserver.py`, `data/raw/` | TSK-M2-01 | **PENDING** |
| **TSK-M2-03** | 02. Data Engineer | P0 | M2 | Flight table parsers (FLEX 284 droplet tests, BASS rods) | `backend/app/ingestion/parsers/` | TSK-M2-02 | **PENDING** |
| **TSK-M2-04** | 02. Data Engineer | P0 | M2 | Pint-based SI unit normalization & non-zero null rule | `backend/app/ingestion/normalizer.py` | TSK-M2-03 | **PENDING** |
| **TSK-M2-05** | 02. Data Engineer | P0 | M2 | Ingestion unit tests & zero-fabrication validation | `backend/tests/test_ingestion.py` | TSK-M2-04 | **PENDING** |
| **TSK-M3-01** | 03. Backend & SI Architect | P0 | M3 | PostgreSQL 16 + pgvector schema models & Alembic migrations | `backend/app/models/`, `backend/alembic/` | TSK-M1-05 | **PENDING** |
| **TSK-M3-02** | 03. Backend & SI Architect | P0 | M3 | Dual-tier database session (Postgres + SQLite fallback) | `backend/app/db/session.py` | TSK-M3-01 | **PENDING** |
| **TSK-M3-03** | 03. Backend & SI Architect | P0 | M3 | FastAPI core application, health & metadata APIs | `backend/app/main.py`, `backend/app/api/v1/endpoints/health.py` | TSK-M3-02 | **PENDING** |
| **TSK-M3-04** | 03. Backend & SI Architect | P0 | M3 | Investigation catalog, detail & faceted filter endpoints | `backend/app/api/v1/endpoints/investigations.py` | TSK-M3-03 | **PENDING** |
| **TSK-M3-05** | 03. Backend & SI Architect | P0 | M3 | Multi-investigation comparison & condition equivalence API | `backend/app/api/v1/endpoints/compare.py` | TSK-M3-04 | **PENDING** |
| **TSK-M3-06** | 03. Backend & SI Architect | P1 | M3 | Analytics & missingness summary API endpoints | `backend/app/api/v1/endpoints/analytics.py` | TSK-M3-05 | **PENDING** |
| **TSK-M4-01** | 05. AI/ML & Data Science | P0 | M4 | FastEmbed ONNX embedding pipeline (`bge-small-en-v1.5`) | `backend/app/ml/embeddings.py` | TSK-M1-04 | **PENDING** |
| **TSK-M4-02** | 05. AI/ML & Data Science | P0 | M4 | Hybrid RRF retrieval (BM25 + vector cosine similarity) | `backend/app/ml/retriever.py` | TSK-M4-01, TSK-M3-01 | **PENDING** |
| **TSK-M4-03** | 05. AI/ML & Data Science | P0 | M4 | Scientific entity & combustion parameter extractor | `backend/app/ml/entity_extractor.py` | TSK-M4-02 | **PENDING** |
| **TSK-M4-04** | 05. AI/ML & Data Science | P0 | M4 | Verifiable citation synthesis linking NASA titles/URLs | `backend/app/ml/citation_engine.py` | TSK-M4-03 | **PENDING** |
| **TSK-M4-05** | 05. AI/ML & Data Science | P0 | M4 | Uncertainty estimation & explicit abstention triggers | `backend/app/ml/abstention.py` | TSK-M4-04 | **PENDING** |
| **TSK-M4-06** | 05. AI/ML & Data Science | P1 | M4 | Scientific intelligence test suite (citations, abstention) | `backend/tests/test_si_pipeline.py` | TSK-M4-05 | **PENDING** |
| **TSK-M5-01** | 04. Frontend & UI/UX | P0 | M5 | Next.js App Router workspace initialization with TypeScript | `frontend/package.json`, `frontend/src/app/` | TSK-M1-04 | **PENDING** |
| **TSK-M5-02** | 04. Frontend & UI/UX | P0 | M5 | Main Research Dashboard & data coverage cards | `frontend/src/app/page.tsx` | TSK-M5-01, TSK-M3-04 | **PENDING** |
| **TSK-M5-03** | 04. Frontend & UI/UX | P0 | M5 | Investigation Explorer with faceted filters & badges | `frontend/src/app/explorer/page.tsx` | TSK-M5-02 | **PENDING** |
| **TSK-M5-04** | 04. Frontend & UI/UX | P0 | M5 | Investigation Detail View with runs & provenance card | `frontend/src/app/investigations/[id]/page.tsx` | TSK-M5-03 | **PENDING** |
| **TSK-M5-05** | 04. Frontend & UI/UX | P0 | M5 | Multi-investigation comparison workspace matrix | `frontend/src/app/compare/page.tsx` | TSK-M5-04, TSK-M3-05 | **PENDING** |
| **TSK-M5-06** | 04. Frontend & UI/UX | P0 | M5 | Evidence-grounded SI chat interface with citation popovers | `frontend/src/app/si-chat/page.tsx` | TSK-M5-05, TSK-M4-04 | **PENDING** |
| **TSK-M5-07** | 04. Frontend & UI/UX | P1 | M5 | Interactive Plotly/Recharts combustion visualizations | `frontend/src/components/charts/` | TSK-M5-06 | **PENDING** |
| **TSK-M6-01** | All Specialists & E2E | P0 | M6 | End-to-end integration pass and 100% test verification | Test reports, CI validation | All Prior Tasks | **PENDING** |
| **TSK-M7-01** | 01. Research & 03. Backend | P0 | M7 | Multi-service Docker Compose deployment configuration | `docker-compose.yml`, service Dockerfiles | TSK-M6-01 | **PENDING** |
| **TSK-M7-02** | 01. Research Architect | P0 | M7 | Final project documentation & 5-minute showcase guide | `docs/PROJECT_ARCHITECTURE.md`, `README.md` | TSK-M7-01 | **PENDING** |
