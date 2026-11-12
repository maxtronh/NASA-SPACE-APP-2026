# Flame in Freefall — Interface Contracts & Source of Truth
**Project**: CORTEXX Scientific Intelligence Platform ("Flame in Freefall")  
**Version**: 1.0.0  
**Status**: Authoritative contract specification (single source of truth)  
**Workspace**: `c:\dev\NASA-SPACE-APP-2026`

---

## 1. Purpose

This document is the **single source of truth** for all interface contracts, database configuration, and schema defaults across the Flame in Freefall platform. Every specialist agent, backend implementation, frontend client, and E2E test must conform to this specification. Any divergence must be escalated to the Project Orchestrator and resolved here before code changes.

---

## 2. Database Configuration (Single Standard)

| Parameter | Value | Notes |
|---|---|---|
| **Primary dialect** | `postgresql+psycopg://` | PostgreSQL 16 + pgvector (production / Docker) |
| **Default DATABASE_URL** | `postgresql+psycopg://flame_user:flame_secure_pass@localhost:5432/flame_freefall` | Canonical credentials |
| **SQLite fallback async** | `sqlite+aiosqlite:///./test_flame.db` | Local offline / Docker-daemon-offline mode |
| **SQLite fallback sync** | `sqlite:///./test_flame.db` | Alembic / sync tooling |
| **Database name** | `flame_freefall` | Must match across docker-compose, config, and tests |
| **DB user** | `flame_user` | Must match across all sources |
| **DB password** | `flame_secure_pass` | Must match across all sources |

**Reconciliation**: All references to `postgres:postgres@localhost:5432/flame_in_freefall` (found in legacy docs and ERROR_LOG.md) are superseded by the canonical `flame_user:flame_secure_pass@localhost:5432/flame_freefall`.

---

## 3. API Base Path

**Prefix**: `/api/v1`

All REST endpoints are mounted under `GET|POST|PUT|DELETE /api/v1/<resource>`.

---

# Project: Flame in Freefall (CORTEXX Scientific Intelligence Platform)
## 4. Endpoint Contracts

### 4.1 Health
**`GET /api/v1/health`**

Response (conforms to `HealthResponse` schema):
```json
{
  "status": "healthy",
  "database": "connected",
  "tier": "postgresql",
  "pgvector_ready": true,
  "version": "1.0.0"
}
```

### 4.2 Investigations Catalog
**`GET /api/v1/investigations`** — Faceted list with pagination and filters: `regime`, `fuel`, `facility`, `gravity_level`, `search`, `limit`, `offset`.

Response (conforms to `PaginatedInvestigationsResponse`):
```json
{
  "total": 0,
  "limit": 20,
  "offset": 0,
  "items": [
    {
      "slug": "string",
      "title": "string",
      "project_acronym": "string",
      "facility": "string",
      "combustion_regime": "string",
      "fuel_type": "string",
      "gravity_level": "string",
      "summary": "string",
      "nasa_source_url": "string",
      "source_repository": "string"
    }
  ]
}
```

**`GET /api/v1/investigations/{id}`** — Detailed investigation profile with runs, measurements, provenance.

Response (conforms to `InvestigationDetailResponse`):
```json
{
  "investigation": { ... },
  "provenance": {
    "source_url": "string",
    "retrieval_timestamp": "ISO-8601",
    "sha256_checksum": "string",
    "original_measurements": { ... },
    "si_measurements": { ... },
    "conversion_method": "deterministic_si_table_v1",
    "validation_status": "VALIDATED"
  },
  "test_runs": [ ... ]
}
```

### 4.3 Ingestion Validation
**`POST /api/v1/ingest/validate`**

Request (conforms to `IngestValidationRequest`):
```json
{
  "investigation": { ... },
  "provenance": { ... }
}
```

Response (conforms to `IngestValidationResponse`):
```json
{
  "status": "valid",
  "slug": "string",
  "checksum_verified": true
}
```

### 4.4 Comparison
**`POST /api/v1/compare`**

Request (conforms to `CompareRequest`):
```json
{
  "investigation_ids": ["uuid-1", "uuid-2"]
}
```
---

## 5. Schema Defaults (Single Standard)

| Field | Canonical Default | Applies To |
|---|---|---|
| `validation_status` | `"VALIDATED"` | `MeasurementRecord` ORM, `ProvenanceRecord` ORM, DTOs |
| `oxidizer_type` | `"Air"` | `Investigation` ORM |
| `source_repository` | `"NASA NTRS"` | `Investigation` ORM |
| `conversion_method` | `"deterministic_si_table_v1"` | `ProvenanceRecord` ORM/DTO |
| `data_completeness_index` | `0.0` | `Investigation` ORM |
| `objectives` | `""` | `Investigation` ORM |

**Reconciliation**: `validation_status` default of `"VALID"` (found in `backend/app/ingestion/models.py`) is superseded by `"VALIDATED"` to match the ORM layer.

---

## 6. Zero-Fabrication & Null Preservation Rules

1. **Missing scientific measurements are `NULL`, never `0.0`.** Parsers map `–`, `N/A`, `null`, and absent tokens to Python `None` / SQL `NULL`.
2. **No synthetic or hardcoded measurements.** All data must originate from verified NASA NTRS / PSI records with SHA-256 provenance.
3. **SHA-256 checksum required** on every ingested raw payload; checksum mismatch → HTTP 422 rejection.
4. **NASA source URLs must resolve to `ntrs.nasa.gov` or `psi.nasa.gov`.**

---

## 7. Ownership & Change Control

| Artifact | Owning Role |
|---|---|
| `PROJECT.md` (this document) | 01. Research & Product Architect (Orchestrator) |
| `backend/app/main.py` + routers | 03. Backend & SI Architect |
| `backend/app/db/session.py` + models | 03. Backend & SI Architect |
| `backend/app/ingestion/` | 02. Data Engineering Specialist |
| `backend/app/ml/` | 05. AI/ML & Data Science Specialist |
| `frontend/` | 04. Frontend & UI/UX Specialist |
| `tests/e2e/` | Independent E2E Testing Track |

Any contract change requires Orchestrator approval and an update to this document before implementation.

---

Response (conforms to `CompareResponse`):
```json
{
  "investigation_ids": ["uuid-1", "uuid-2"],
  "equivalence_assessment": {
    "equivalent": false,
    "reasons": ["gravity_level mismatch: microgravity vs 1g"]
  },
  "comparison_grid": { ... }
}
```

### 4.5 Analytics
**`GET /api/v1/analytics/corpus`**

Response (conforms to `CorpusAnalyticsResponse`):
```json
{
  "total_investigations": 0,
  "combustion_regimes": { "droplet_combustion": 1, ... },
  "missing_data_matrix": {
    "radiative_flux": { "present_count": 0, "missing_count": 1, "completeness_pct": 0.0 }
  }
}
```

### 4.6 Scientific Intelligence Query
**`POST /api/v1/si/query`**

Request (conforms to `SIQueryRequest`):
```json
{
  "query": "string",
  "filters": { ... }
}
```

Response (conforms to `SIQueryResponse`):
```json
{
  "query": "string",
  "answer": "string",
  "confidence_score": 0.0,
  "abstention_flag": false,
  "citations": [
    {
      "investigation_id": "string",
      "title": "string",
      "nasa_source_url": "string",
      "relevance_score": 0.0
    }
  ],
  "explainability": {
    "matched_entities": [],
    "retrieval_method": "hybrid_rrf_bm25_vector",
    "abstention_reason": null
  }
}
```

---


## Architecture Overview
Flame in Freefall is an advanced Scientific Intelligence (SI) platform leveraging NASA microgravity combustion research data (from PSI, NTRS, Glenn Research Center) to enable multi-investigation discovery, scientific condition comparison, evidence retrieval, data analysis, and explainable insights.

### Core Architectural Layers
1. **Data Ingestion & Provenance Engine**: Repeatable 7-phase pipeline (Discover, Fetch, Preserve, Parse, Normalize, Validate, Index) extracting authentic NASA records from NTRS REST API and PSI archives. Strict zero-fabrication and null-preservation policy.
2. **Database Layer**: PostgreSQL 16 with pgvector extension (with SQLite/NumPy fallback for local unit test resilience). Schema covers `investigations`, `test_runs`, `measurements`, `literature_citations`, `provenance_records`, and `vector_embeddings`.
3. **Backend Services (FastAPI)**: Modular REST API exposing endpoints for health, faceted exploration, multi-condition comparison, corpus analytics, and evidence-grounded SI queries.
4. **Scientific Intelligence & ML**: 7-stage evidence-first pipeline utilizing local ONNX sentence embeddings (`fastembed`), BM25 + pgvector hybrid retrieval with Reciprocal Rank Fusion (RRF), scientific entity extraction, explicit abstention/uncertainty engine, and citation verification.
5. **Interactive Frontend (Next.js & TypeScript)**: App router frontend with Tailwind CSS, Recharts, and Plotly.js for interactive scientific exploration (droplet $d^2$ burning curves, flame spread velocities, completeness matrices, comparison workspace, and SI chat).
6. **Independent E2E Testing Track**: Dual-track 4-tier testing framework guaranteeing end-to-end user journey integrity, API conformance, and citation verification.

---

## 🔒 Configuration & Database Standards
- **Standard Database Connection**:
  - `DATABASE_URL`: `postgresql+psycopg://flame_user:flame_secure_pass@localhost:5432/flame_freefall`
  - Fallback Dialect: `sqlite+aiosqlite:///./test_flame.db` (for local unit tests when Docker is offline)
- **Validation Status Enum Standard**:
  - `VALIDATED`: Record verified authentic with checksum and physical SI bounds
  - `EXTINCTION_UNOBSERVED`: Test concluded without visible droplet extinction
  - `DISRUPTION`: Bubble disruption/ejection terminated test early
  - `SENSOR_SATURATED`: Signal exceeded sensor dynamic range
  - `MISSING_DATA`: Field unrecorded in NASA flight archives (stored as `NULL`, never `0.0`)
- **Anti-Hallucination & Non-Zero Policy**:
  - Missing measurements are strictly `None` / `NULL`. Zero substitution is prohibited.

---

## 🔒 Five Specialist Roles & Ownership
| # | Role | Specialist Scope | Key Deliverables | File Ownership |
|---|------|------------------|------------------|----------------|
| 1 | **Research Architect** | NASA research catalog, source validation, requirements, environment audit | `docs/*`, `PROJECT_TASKS.md`, `PROJECT_PROGRESS.md`, `ERROR_LOG.md` | `docs/`, `*.md` |
| 2 | **Data Engineer** | NASA ingestion pipeline, SI normalization, data validation, provenance | Ingestion scripts, raw data lake, SI conversion module, provenance tracking | `data/`, `scripts/`, `backend/app/ingestion/`, `backend/tests/test_ingestion.py` |
| 3 | **Backend & SI Architect** | FastAPI backend, PostgreSQL + pgvector, hybrid search API, comparison service | `backend/app/`, Alembic migrations, database models, REST endpoints, backend unit/integration tests | `backend/alembic/`, `backend/app/models/`, `backend/app/db/`, `backend/app/api/`, `backend/app/services/` |
| 4 | **Frontend & UI/UX Specialist** | Next.js frontend, dashboard, explorer, comparison workspace, SI chat, charts | `frontend/`, interactive pages, Plotly/Recharts components, API client integration | `frontend/` |
| 5 | **AI/ML & Data Science Specialist** | Embeddings, hybrid ranking, uncertainty engine, explainability, analytics | `backend/app/ml/`, FastEmbed integration, RRF hybrid retrieval, entity extractor, abstention engine | `backend/app/ml/` |
| - | **E2E Testing Orchestrator** | Independent opaque-box test suite (Tiers 1-4) & Tier 5 adversarial testing | `TEST_INFRA.md`, automated E2E test harness (`tests/e2e/`), `TEST_READY.md` | `tests/e2e/`, `TEST_READY.md` |

---

## 🔒 Milestones Status
| # | Milestone Name | Scope | Dependencies | Status | Key Outputs / Evidence |
|---|----------------|-------|--------------|--------|------------------------|
| M0 | Survey & Planning | Environment audit, NASA specs, architecture exploration | none | **DONE** | 3 survey reports, `PROJECT.md`, `TEST_INFRA.md` |
| M1 | Research & Product Architecture | Architecture docs, schemas, roadmaps, task boards, Git & Python setup | M0 | **DONE** | `docs/ENVIRONMENT_AUDIT.md`, `NASA_RESEARCH_LOG.md`, `.venv`, `.git` |
| M-E2E | E2E Testing Track | Independent 4-tier opaque-box test suite | M1 | **DONE** | `tests/e2e/` (83 tests), `TEST_READY.md` published |
| M2 | NASA Data Ingestion Pipeline | Ingestion engine, SI normalization, SHA-256 provenance | M1 | **DONE** | 300 test runs, 1208 measurements, FLEX 20150023456 verified |
| M3 | Database & Backend Architecture | FastAPI app mounting, Alembic migrations, CRUD endpoints | M1, M2 | **DONE** | `0001_initial_schema.py` head, `backend/app/main.py`, 48 backend tests passed |
| BASELINE | Git Baseline & E2E Live Verification | Initial commit, live backend E2E execution | M2, M3, M-E2E | **DONE** | Commit `9b04e06`, 83/83 E2E passed against live `backend.app.main:app` |
| M4 | AI/ML & Data Science | FastEmbed ONNX, RRF hybrid retrieval, entity extractor, abstention engine | M2, M3 | **DONE** | `backend/app/ml/`, 63 backend tests passed |
| M5 | Frontend and UI/UX | Next.js 15 App Router, 6 views, Plotly d² burning curves, comparison, chat | M1, M3 | **DONE** | `frontend/src/app/`, `npm run build` exit 0 (8 routes) |
| M6 | Full System Integration & Validation | Full-stack live test, Tier 5 adversarial hardening, Forensic Audit | M4, M5 | **PLANNED** | Live integration pass, forensic audit report |
| M7 | Deployment & Showcase Materials | Docker Compose multi-stage build, demo runbook, presentation materials | M6 | **DONE** | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `README.md` |

---

## Interface Contracts

### 1. Data Ingestion Output -> Database Schema
```json
{
  "investigation": {
    "slug": "acme-cld-flame",
    "title": "Coflow Laminar Diffusion Flame",
    "project_acronym": "ACME",
    "facility": "Combustion Integrated Rack (CIR)",
    "combustion_regime": "laminar_diffusion",
    "fuel_type": "Methane (CH4)",
    "gravity_level": "microgravity (~10^-6 g)",
    "summary": "...",
    "nasa_source_url": "https://ntrs.nasa.gov/citations/20190001859",
    "source_repository": "NASA NTRS"
  },
  "provenance": {
    "source_url": "https://ntrs.nasa.gov/citations/20190001859",
    "retrieval_timestamp": "2026-11-12T18:00:00Z",
    "sha256_checksum": "a8f3b...",
    "original_measurements": {"fuel_flow_rate": "25 sccm", "soot_volume_fraction": null},
    "si_measurements": {"fuel_flow_rate_m3_s": 4.16667e-7, "soot_volume_fraction_dimensionless": null},
    "conversion_method": "deterministic_si_table_v1",
    "validation_status": "VALIDATED"
  }
}
```

### 2. Backend REST API Contracts
- `GET /health` & `GET /api/v1/health`: Returns `{"status": "healthy", "database": "connected", "pgvector_ready": true, "version": "1.0.0"}`
- `GET /api/v1/investigations`: Query params `regime`, `fuel`, `facility`, `gravity`, `search`, `limit`, `offset`. Returns `{"total": int, "limit": int, "offset": int, "items": [...]}`
- `GET /api/v1/investigations/{id_or_slug}`: Returns full investigation details, trials, measurements, citations, and provenance.
- `POST /api/v1/compare`: Body `{"investigation_ids": ["slug1", "slug2"]}`. Returns comparative parameter grid and `equivalence_assessment`.
- `POST /api/v1/si/query`: Body `{"query": "What causes soot reduction in microgravity methane flames?"}`.
  Returns:
  ```json
  {
    "query": "...",
    "answer": "...",
    "confidence_score": 0.88,
    "abstention_flag": false,
    "citations": [
      {
        "investigation_id": "acme-cld-flame",
        "title": "Coflow Laminar Diffusion Flame",
        "nasa_source_url": "https://ntrs.nasa.gov/citations/20190001859",
        "relevance_score": 0.92
      }
    ],
    "explainability": {
      "matched_entities": ["soot reduction", "microgravity", "methane"],
      "retrieval_method": "hybrid_rrf_bm25_vector"
    }
  }
  ```
- `GET /api/v1/analytics/corpus`: Returns `{"total_investigations": int, "combustion_regimes": dict, "missing_data_matrix": dict}`.

---

## Code Layout
```
c:\dev\NASA-SPACE-APP-2026\
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── ingestion/
│   │   └── ml/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   ├── package.json
│   └── tsconfig.json
├── data/
│   ├── raw/
│   └── processed/
├── scripts/
│   ├── ingest_nasa_data.py
│   └── validate_provenance.py
├── docs/
├── tests/
│   └── e2e/
├── docker-compose.yml
├── PROJECT.md
├── TEST_READY.md
├── PROJECT_TASKS.md
├── PROJECT_PROGRESS.md
└── ERROR_LOG.md
```
