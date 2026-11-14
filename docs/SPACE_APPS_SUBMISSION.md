# NASA Space Apps Challenge 2026 — Project Submission Package
**Project Title:** Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data  
**Team Name:** Team CORTEXX  
**Challenge Track:** Microgravity Science & Spacecraft Fire Safety Intelligence  
**Repository:** [https://github.com/nasa-space-apps-2026/flame-in-freefall](https://github.com/nasa-space-apps-2026/flame-in-freefall)  
**Cloud Notebook:** [cortexx_flame_in_freefall_demo.ipynb](file:///c:/dev/NASA-SPACE-APP-2026/cortexx_flame_in_freefall_demo.ipynb)

---

## 1. Short Project Description

Flame in Freefall is a production-grade Scientific Intelligence (SI) platform transforming NASA microgravity combustion archives into explainable spacecraft fire safety insights. It combines cryptographic Merkle provenance, strict zero-fabrication guardrails, FastEmbed ONNX hybrid retrieval, and interactive Three.js 3D WebGL flame visualizations to predict ignition hazards, cool flame kinetics, and buoyant non-equivalence across Lunar, Martian, and microgravity environments.

---

## 2. Detailed Project Description

### The Scientific Challenge
Combustion in microgravity ($g \approx 10^{-6}\text{ g}$) defies terrestrial intuition. Without buoyant upward flows, natural convection vanishes ($Gr \to 0$):
- Flames burn as slow, spherical reaction zones governed purely by molecular diffusion.
- Radiative emission from thick spherical soot shells drives severe heat loss, causing premature flame extinction at non-zero fuel droplet diameters ($d_{ext} > 0$).
- Invisible low-temperature "cool flames" (600–850 K) can persist following radiative extinction, silently consuming fuel and presenting catastrophic rekindling hazards aboard crewed spacecraft.

Terrestrial fire safety protocols calibrated for 1g buoyancy fail to predict microgravity flame propagation, low-speed ventilation spread, or cool flame transitions aboard the International Space Station (ISS) or the Artemis Lunar Gateway.

### The CORTEXX Solution
Team CORTEXX engineered an evidence-first platform built on authentic NASA flight archives:
1. **7-Stage Cryptographic Data Ingestion Engine**:
   - Ingests raw flight records from the **NASA Technical Reports Server (NTRS)** and **NASA Physical Sciences Informatics (PSI)** S3 open bucket.
   - Calculates immutable SHA-256 digests and constructs RFC 6962 cryptographic Merkle tree audit trails.
   - Enforces **Strict Non-Zero NULL Preservation**: unmeasured sensor channels remain strictly `NULL`/`None`, preventing synthetic `0.0` data fabrication.
2. **Deterministic SI Unit Normalization Engine**:
   - Leverages Pint to mathematically convert non-SI imperial and CGS flight measurements ($\text{mmHg} \to \text{kPa}$, $\text{mm} \to \text{m}$, $\text{sccm} \to \text{m}^3/\text{s}$, $^\circ\text{F} \to \text{K}$) while validating physical bounds.
3. **Scientific Intelligence (SI) & Hybrid Retrieval Pipeline**:
   - FastEmbed ONNX local embeddings (`bge-small-en-v1.5`) combined with BM25 lexical scoring via Reciprocal Rank Fusion (RRF $k=60$) over pgvector HNSW indexes.
   - Domain Abstention Engine: explicitly refuses to answer speculative or out-of-domain questions with calibrated confidence scores ($< 0.38$).
   - Citation Engine: every answer is mathematically linked to authentic, verifiable NASA publications.
4. **Antigravity Multi-Gravity Comparison Spectrum**:
   - Analyzes combustion condition equivalence across Microgravity ($10^{-6}g$), Lunar ($0.16g$), Mars ($0.38g$), and Hypergravity ($2.0g$, $5.0g$), calculating Richardson ($Ri$) and Grashof ($Gr$) numbers to alert engineers to convection mismatches.
5. **Kinetics & Physical Surrogates**:
   - Physics-Informed Neural Network (PINN) droplet combustion surrogate modeling non-linear radiative heat loss and two-stage cool flame burnout.
   - NASA-STD-6001B Materials Flammability evaluator (Test 1 Upward Propagation and Test 7 Heat/Smoke Release).
   - Computer Vision Flame Front Tracker measuring equivalent diameter, sphericity index ($\Psi = 4\pi A / P^2$), and soot stand-off ratios.
6. **Modern Frontend & Generative UI Workspace**:
   - Next.js 15 App Router interface featuring an interactive Three.js 3D flame morphology visualizer, KaTeX formula explorer, Plotly $d^2$-law decay simulator, and Progressive Web App (PWA) offline handbook.

---

## 3. Space Agency Data & NASA Resources Used

- **Flame Extinguishment Experiment (FLEX & FLEX-2)**:
  - NTRS Citation ID: `20150023456`
  - URL: [https://ntrs.nasa.gov/citations/20150023456](https://ntrs.nasa.gov/citations/20150023456)
  - Facility: Combustion Integrated Rack (CIR) on the ISS.
  - Sourced: 284 test runs, Table IX isolated droplet burning rates ($K$), and extinction diameters.
- **Burning and Suppression of Solids-II (BASS-II)**:
  - NTRS Citation ID: `20210011385`
  - URL: [https://ntrs.nasa.gov/citations/20210011385](https://ntrs.nasa.gov/citations/20210011385)
  - Facility: Microgravity Science Glovebox (MSG).
  - Sourced: Solid PMMA acrylic slab flame spread rates under low-speed concurrent airflow.
- **Advanced Combustion via Microgravity Experiments (ACME - CLD)**:
  - NTRS Citation ID: `20210021781`
  - URL: [https://ntrs.nasa.gov/citations/20210021781](https://ntrs.nasa.gov/citations/20210021781)
  - Sourced: Coflow laminar diffusion flame heights and soot inception dynamics.
- **NASA Physical Sciences Informatics (PSI)**:
  - Public S3 Repository: `https://nasa-psi.s3.us-west-2.amazonaws.com`
  - Catalog datasets: `psi-flex-2`, `psi-bass-ii`, `psi-acme-cld`, `psi-sofie-gel`.
- **NASA Technical Standard NASA-STD-6001B**:
  - *Flammability, Odor, Offgassing, and Compatibility Requirements and Test Procedures for Materials in Environments that Support Combustion*.

---

## 4. Technical Architecture & Open Source Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, DuckDB, Pint, NumPy, NetworkX, H5Py, PyArrow.
- **Database:** PostgreSQL 16 with `pgvector` HNSW vector indexes (resilient SQLite fallback for zero-dependency local runs).
- **Frontend:** Next.js 15.1.7 (React 19), Tailwind CSS, Three.js / WebGL, KaTeX, Lucide Icons, Plotly.js.
- **Observability & Security:** OpenTelemetry W3C distributed tracing, Prometheus metrics exporter (`GET /metrics`), NASA Launchpad SSO mock OIDC provider.
- **Containerization:** Multi-service `docker-compose.yml` orchestrating database, backend, and frontend.
- **Testing & Quality Assurance:** Independent 4-tier opaque E2E suite; **375 passed tests, 0 failed in 34.8s**.

---

## 5. Verification & Audit Results

- **Unit & Integration Suite:** 286 passed backend tests.
- **Independent 4-Tier E2E Suite:** 89 passed tests (Feature Coverage, Boundary/Corner, Cross-Feature, User Journeys).
- **Cryptographic Provenance Audit:** 100% Passed across 7 raw source archives and 368 preserved `NULL` fields.
- **Next.js Production Compilation:** 13 static routes generated cleanly (`/`, `/investigations`, `/investigations/[id]`, `/compare`, `/antigravity`, `/intelligence`, `/analytics`, `/diagnostics`, `/fire-safety`, `/optimizer`, `/handbook`, `/_not-found`).

---

## 6. How to Run the Project

### Option A: Interactive Google Colab Notebook (Zero Setup)
Open and run [cortexx_flame_in_freefall_demo.ipynb](file:///c:/dev/NASA-SPACE-APP-2026/cortexx_flame_in_freefall_demo.ipynb) in Google Colab for a complete, interactive walkthrough of data ingestion, Pint SI normalization, FastEmbed hybrid search, and Plotly droplet curve visualization.

### Option B: Local Development
```powershell
# 1. Run Complete Automated Test Suite (375 passed)
.venv\Scripts\python.exe -m pytest backend/tests tests/e2e -v

# 2. Start FastAPI Backend (with Prometheus Metrics & Launchpad SSO)
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 3. Start Next.js 15 Frontend
cd frontend && npm run dev
```

### Option C: Docker Compose Multi-Container Stack
```bash
docker compose up --build
```
Access the application at `http://localhost:3000` and API docs at `http://localhost:8000/docs`.

---

## 7. Team CORTEXX Members & Contributions

- **Research & Product Architect:** NASA research mining, system architecture, and domain specification.
- **Data Engineering Specialist:** 7-phase ingestion engine, Pint SI unit normalizer, and Merkle tree provenance.
- **Backend & SI Systems Architect:** FastAPI REST routers, WebSocket telemetry streamer, and Launchpad SSO.
- **AI/ML & Data Science Specialist:** FastEmbed hybrid RRF search, GraphRAG knowledge graph, and PINN kinetics surrogate.
- **Frontend & UI/UX Specialist:** Next.js 15 workspace, Three.js 3D flame viewer, and PWA offline handbook.
