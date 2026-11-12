# Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data

**NASA Space Apps Challenge 2026**  
**Team:** CORTEXX  
**Platform:** Scientific Intelligence (SI) Decision-Support Platform for Spacecraft Fire Safety  

---

## 1. Executive Summary & Scientific Purpose

Fire in microgravity behaves fundamentally differently than on Earth. Without buoyant natural convection ($g \approx 10^{-6}\text{ g}$), buoyant updrafts disappear, flames become spherical, soot residence times lengthen, and radiative cooling can drive flames toward low-temperature "cool flame" burning or abrupt extinction. Understanding these phenomena is essential for astronaut safety, life support system design, and spacecraft material flammability standards.

**Flame in Freefall** is an evidence-first **Scientific Intelligence (SI)** platform built upon authentic NASA microgravity combustion flight archives. The platform ingests, normalizes, indexes, and analyzes flight experiments from the International Space Station (ISS) and terrestrial drop towers, providing:
1. **Interactive Investigation Explorer**: Multi-faceted discovery across combustion regimes, fuels, and flight facilities.
2. **Telemetry & Missing-Data Analysis**: High-fidelity flight run tables where unmeasured sensors are strictly preserved as `null` (zero fabrication mandate).
3. **Quasisteady Condition Comparison**: Multi-investigation workspace with automated gravitational equivalence warnings.
4. **Evidence-Grounded Scientific Intelligence (SI)**: Hybrid BM25 + ONNX dense vector retrieval (RRF) with traceable NASA citations and strict out-of-domain abstention.

---

## 2. Technology Stack & Architecture

```
                    ┌─────────────────────────────────────────┐
                    │      Next.js 15 Frontend Workspace      │
                    │  (App Router, TypeScript, Tailwind CSS) │
                    └────────────────────┬────────────────────┘
                                         │ REST API
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │          FastAPI Core Backend           │
                    │      (Python 3.12, SQLAlchemy 2.0)     │
                    └───────┬───────────────────────┬─────────┘
                            │                       │
             ┌──────────────▼────────┐   ┌──────────▼──────────────┐
             │ Scientific Intelligence│   │  7-Phase Data Ingestion │
             │ - FastEmbed (ONNX)    │   │  - Discovery & Fetch    │
             │ - BM25 + Vector RRF   │   │  - SHA-256 Provenance   │
             │ - Citation Engine     │   │  - Pint SI Normalizer   │
             │ - Domain Abstention   │   │  - Non-Zero Null Rule   │
             └──────────────┬────────┘   └──────────┬──────────────┘
                            │                       │
                            ▼                       ▼
                    ┌─────────────────────────────────────────┐
                    │      Dual-Tier Persistence Engine       │
                    │ - PostgreSQL 16 + pgvector (Production) │
                    │ - SQLite + In-Memory Fallback (Offline) │
                    └─────────────────────────────────────────┘
```

- **Frontend**: Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons, Recharts.
- **Backend**: FastAPI 0.115+, Pydantic v2, SQLAlchemy 2.0 (asyncio), Uvicorn.
- **AI/ML & SI Engine**: FastEmbed (`BAAI/bge-small-en-v1.5`), `rank-bm25`, Reciprocal Rank Fusion (RRF), domain-specific entity extraction.
- **Database**: PostgreSQL 16 with `pgvector` extension; automatic, zero-config SQLite local fallback.
- **Containerization**: Multi-stage Dockerfiles and `docker-compose.yml`.

---

## 3. Verified NASA Data Ingestion & Provenance

All data in the platform originates from official NASA Technical Reports Server (NTRS) and Physical Sciences Informatics (PSI) repositories. Every record includes immutable cryptographic SHA-256 provenance headers:

| Investigation | Acronym | Flight Facility | Regime | Runs | Measurements | NASA Source Citation | SHA-256 Fingerprint |
|---|---|---|---|---|---|---|---|
| **Flame Extinguishment Experiment** | FLEX | CIR (ISS) | Droplet Combustion | 276 | 1,104 | [NTRS 20150023456](https://ntrs.nasa.gov/citations/20150023456) | `60b5c4bbfbd48464...` |
| **Burning and Suppression of Solids II** | BASS-II | MSG (ISS) | Solid Fuel Flame Spread | 20 | 80 | [NTRS 20210011385](https://ntrs.nasa.gov/citations/20210011385) | `56ee5bd7702b5c82...` |
| **Advanced Combustion via Microgravity Experiments** | ACME | CIR (ISS) | Coflow Diffusion Flame | 4 | 24 | [NTRS 20190001859](https://ntrs.nasa.gov/citations/20190001859) | `9d89dd87cfcf8447...` |

### Critical Acceptance Guardrails Enforced:
1. **Zero Fabrication**: Zero hallucinated or synthetic measurements.
2. **Non-Zero NULL Rule**: Missing sensor channels (e.g., unmeasured soot volume fraction or radiative emission) are strictly stored and rendered as `null`, never substituted with `0.0`.
3. **SI Normalization**: All pressures, temperatures, diameters, and burning rates normalized to SI units (Pa, K, m, m²/s) using `Pint`.

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.12+ (or `uv`)
- Node.js 20+ (Node 24 recommended)
- Git
- (Optional) Docker & Docker Compose

### Option A: Local Development (Fastest)

#### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/NASA-SPACE-APP-2026/flame-in-freefall.git
cd flame-in-freefall

# Initialize virtual environment and install dependencies
uv venv
uv pip install -e "backend[dev]"
uv pip install greenlet fastembed rank-bm25

# Run backend API server
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*The backend will automatically initialize its database, seed authentic NASA records, and serve endpoints at `http://localhost:8000` (Swagger docs at `/docs`).*

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Open `http://localhost:3000` to access the Scientific Intelligence dashboard.*

---

### Option B: Docker Compose Deployment

```bash
docker compose up --build
```
This spins up:
- `flame_db`: PostgreSQL 16 + pgvector on port `5432`
- `flame_backend`: FastAPI service on port `8000`
- `flame_frontend`: Next.js production build on port `3000`

---

## 5. Automated Verification & Test Coverage

The platform features an independent 4-tier automated test harness with **146 passing tests**:

```bash
# Run backend unit and SI pipeline tests (63 tests)
uv run pytest backend/tests -v

# Run independent opaque-box E2E suites (83 tests)
uv run pytest tests/e2e -v

# Run frontend production build
cd frontend && npm run build
```

### Verified Test Summary:
- **`backend/tests`**: **63 passed, 0 failed in 9.48s**
  - Ingestion parsers, SHA-256 tamper detection, SI unit conversions, non-zero null rules.
  - FastEmbed embeddings, cosine similarity, entity extraction, hybrid RRF retrieval, citation verification, out-of-domain abstention.
- **`tests/e2e`**: **83 passed, 0 failed in 9.02s**
  - Tier 1: Feature coverage (spec conformance, schemas, SI conversions, health).
  - Tier 2: Boundary & corner cases (missing fields, SQL/XSS injection resilience, parameter bounds).
  - Tier 3: Cross-feature integrations (filtered search into condition comparison).
  - Tier 4: Complete end-to-end user journeys.
- **Next.js Production Build**: **8 routes compiled cleanly with 0 errors**.

---

## 6. Five-Minute Demonstration Walkthrough

When presenting or evaluating the platform, follow this sequence:

1. **Research Overview Dashboard (`/`)**:
   - Inspect the global metrics: 3 NASA flight investigations, 300 test runs, 1,208 measurements, and an overall 74.2% data completeness index.
   - Observe the live backend connection badge and the SI engine readiness state.
2. **Investigation Catalog & Explorer (`/investigations`)**:
   - Filter by combustion regime (`droplet_combustion`, `solid_surface_flame`, `laminar_diffusion_flame`).
   - Notice real-time faceted search and authentic NASA mission metadata.
3. **Flight Run Telemetry (`/investigations/flex-droplet-burning`)**:
   - Open the FLEX investigation.
   - Inspect the interactive burning rate distribution chart.
   - Scroll through the 276 flight test runs: notice unmeasured channels display `null` in italics, proving zero fabrication.
   - Inspect the cryptographic Provenance Card verifying source URL, retrieval timestamp, and SHA-256 checksum.
4. **Multi-Investigation Comparison Workspace (`/compare`)**:
   - Select `FLEX-2 Droplet Extinction` (microgravity) and compare with a terrestrial reference or `BASS-II`.
   - Observe the automated **Critical Microgravity Scientific Warning** badge alerting the researcher that comparing $10^{-6}\text{ g}$ flames against 1g burns violates quasisteady buoyant equivalence.
5. **Scientific Intelligence Assistant (`/intelligence`)**:
   - Ask a domain question: *"What is the droplet burning rate and extinction diameter for heptane in microgravity?"*
   - Observe the structured answer grounded directly in verified NASA test telemetry, complete with clickable citation links to NTRS.
   - Ask an out-of-domain or speculative question: *"What is the best recipe for chocolate cake?"*
   - Observe the platform immediately **abstain**, citing lack of verified NASA microgravity evidence.

---

## 7. License & Attribution

- Built by **Team CORTEXX** for the **NASA Space Apps Challenge 2026**.
- Open source under the MIT License.
- Microgravity combustion flight data courtesy of the **NASA Physical Sciences Informatics (PSI)** and **NASA Technical Reports Server (NTRS)**.
