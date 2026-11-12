# Flame in Freefall — Development Tools and Repositories
**Deliverable**: R1 System & Environment Documentation  
**Version**: 1.0.0  
**Author**: 01. Research and Product Architect  
**Workspace**: `c:\dev\NASA-SPACE-APP-2026`  

---

## 1. Overview and Technology Selection Rationale

The "Flame in Freefall" architecture is engineered to satisfy NASA Space Apps competition criteria and rigorous scientific computing standards. The platform ingests, normalizes, indexes, queries, and visualizes authentic spaceflight combustion datasets (FLEX, ACME, BASS, SoFIE).

To guarantee reliability, deterministic execution, and sub-second latency under local desktop resource constraints (~15 GB RAM, Windows 11 host), every tool, library, and framework in our stack has been evaluated against:
1. **Scientific Veracity & Accuracy**: Deterministic dimensional conversion (Pint), zero data fabrication, exact citation provenance.
2. **Resource Efficiency**: CPU-friendly ONNX embeddings (FastEmbed), lightweight ASGI runtime (FastAPI), zero-dependency client bundles.
3. **Resilience**: Dual-tier storage (PostgreSQL 16 + pgvector in container, SQLite + numpy vector fallback for offline tests).
4. **Developer Ergonomics & Typing**: Strict TypeScript in frontend, Pydantic v2 and SQLAlchemy 2.0 type safety in backend.

---

## 2. Approved Technology Stack Matrix

| Category | Primary Technology | Version | Purpose & Architectural Role | Alternative Considered | Selection Justification |
|---|---|---|---|---|---|
| **Python Tooling** | `uv` | `0.13.7` | Fast virtualenv and dependency resolution | `poetry`, `pipenv`, `conda` | 10–100x faster than standard pip; native Windows binary; perfect lockfile determinism. |
| **Backend Framework** | `FastAPI` | `0.162.x` | Asynchronous REST API service for scientific intelligence | `Django`, `Flask` | Native OpenAPI schemas, Pydantic v2 validation, high concurrency for data streaming and search. |
| **Data Validation** | `Pydantic v2` | `2.14.x` | Type enforcement, serialization, and boundary checks | `Marshmallow`, `Cerberus` | High-speed Rust core (`pydantic-core`), strict constraint checks (e.g. $P > 0$, $T > 0$). |
| **Relational ORM** | `SQLAlchemy` | `2.1.x` | Type-annotated relational modeling & query generation | `Tortoise-ORM`, `Peewee` | Robust migration support, dialect independence (Postgres/SQLite), seamless pgvector integration. |
| **Database Driver** | `psycopg` (v3) | `3.3.x` | Modern async/sync PostgreSQL driver with binary wheels | `asyncpg`, `psycopg2` | Full PostgreSQL 16 feature support, native Python typing, precompiled binary wheels on Windows. |
| **Vector Storage** | `pgvector` | `0.5.1` | In-database vector indexing and cosine distance search | `ChromaDB`, `Pinecone`, `Milvus` | Zero operational overhead; unifies relational metadata and vector embeddings in a single ACID transaction. |
| **Dimensional Analysis** | `Pint` | `0.26.x` | Deterministic SI unit conversion and dimensional checks | Handcrafted conversion multipliers | Formal physical unit registry; prevents unit mismatch errors across aerospace and imperial units. |
| **Vector Embeddings** | `FastEmbed` | `0.9.x` | Local ONNX-based sentence embeddings (`BAAI/bge-small-en-v1.5`) | `sentence-transformers` (PyTorch) | Uses ONNX Runtime; requires <150 MB RAM; eliminates heavy PyTorch installation (>2 GB disk, high RAM). |
| **Scientific Computing**| `NumPy` & `SciPy` | `2.5.x` / `1.18.x` | Regression fitting ($d^2(t)$ burning rates) and numerical algorithms | Plain Python loops | C-optimized matrix math, non-linear least squares optimization (`scipy.optimize.curve_fit`). |
| **Data Analytics** | `Pandas` | `3.1.x` | Investigation parameter summarization and missingness profiling | Custom dictionary aggregation | Standard DataFrame manipulation, multi-faceted grouping, CSV export routines. |
| **Frontend Framework** | `Next.js` | `15.x / 16.x` | Server and client rendering, App Router architecture | `Vite + React SPA`, `Nuxt` | Modular layout, built-in server component optimizations, rich ecosystem. |
| **Frontend Language** | `TypeScript` | `5.x` | Compile-time type safety across UI components and API payloads | Vanilla JavaScript | Prevents runtime schema mismatch between backend API responses and frontend state. |
| **Styling & Theme** | `Tailwind CSS` | `3.4.x / 4.x` | Scientific aerospace dashboard styling and layout utility | `Bootstrap`, `Material UI` | Highly customizable, minimal CSS bundle overhead, zero runtime CSS-in-JS performance penalty. |
| **Data Visualization** | `Plotly.js` & `Recharts` | `4.3.x` / `3.10.x` | Droplet burning curves ($d^2(t)$) and interactive telemetry | `Chart.js`, `D3.js` | Plotly provides high-precision scientific plotting; Recharts provides lightweight reactive React charts. |
| **Testing Suite** | `pytest` & `pytest-asyncio` | `9.2.x` / `1.5.x` | Asynchronous backend API and unit test validation | `unittest` | Rich fixtures, parameterized testing, async endpoint testing via `httpx.AsyncClient`. |
| **Code Formatting** | `Ruff` | `0.17.x` | Blazing-fast Python linting and code formatting | `flake8`, `black`, `isort` | Instant feedback, unified linter/formatter, zero dependency overhead. |

---

## 3. Verified NASA Portals & Open-Source Repositories

### 3.1 NASA Scientific Data Sources
1. **NASA Technical Reports Server (NTRS)**
   - **Portal URL**: `https://ntrs.nasa.gov/`
   - **REST API Endpoint**: `https://ntrs.nasa.gov/api/citations/search`
   - **Citation Details**: `https://ntrs.nasa.gov/api/citations/{id}`
   - **Asset Download**: `https://ntrs.nasa.gov/api/citations/{id}/downloads/{filename}`
   - **Capabilities Verified**: Free, unauthenticated REST API, rich parametric search (`center=GRC`, `stiType=TECHNICAL_PUBLICATION`), direct extraction of full experimental text files (`.txt`), rate limit tracking (`X-RateLimit-Limit: 500`).
2. **NASA Physical Sciences Informatics (PSI)**
   - **Portal URL**: `https://psi.nasa.gov/` (redirects to `https://science.nasa.gov/biological-physical/data/`)
   - **AWS S3 Public Mirror**: `https://nasa-psi.s3.us-west-2.amazonaws.com/` (`s3://nasa-psi/`)
   - **Capabilities Verified**: Public AWS Open Data repository hosting raw data files from flight experiments in physical sciences.
3. **NASA Glenn Research Center (GRC)**
   - **Division URL**: `https://www.nasa.gov/glenn/`
   - **Combustion Branch Focus**: Microgravity combustion physics, drop towers (2.2s and 5.1s Zero-G Facility), ISS Combustion Integrated Rack (CIR).

### 3.2 Key Open-Source Repositories
1. **pgvector (PostgreSQL vector similarity search)**:
   - **Repository**: `https://github.com/pgvector/pgvector`
   - **License**: PostgreSQL License (Open Source)
   - **Docker Image**: `pgvector/pgvector:pg16`
2. **Pint (Python physical quantities and unit manipulation)**:
   - **Repository**: `https://github.com/hgrecco/pint`
   - **License**: BSD 3-Clause
3. **FastEmbed (Fast, CPU-optimized sentence embedding generation)**:
   - **Repository**: `https://github.com/qdrant/fastembed`
   - **License**: Apache 2.0
   - **Default Model**: `BAAI/bge-small-en-v1.5` (384-dimensional cosine embeddings)
4. **FastAPI (Modern Python web framework)**:
   - **Repository**: `https://github.com/fastapi/fastapi`
   - **License**: MIT
5. **Next.js (The React framework for the Web)**:
   - **Repository**: `https://github.com/vercel/next.js`
   - **License**: MIT

---

## 4. Model Context Protocol (MCP) and Agent Integrations

The development workflow and automated agents operate with structured MCP server extensions to maintain state grounding and verification:
- **Filesystem MCP**: Safe read/write operations constrained to `c:\dev\NASA-SPACE-APP-2026`.
- **Fetch MCP**: Live HTTP querying to probe upstream NASA APIs, verify status codes, and test ETag headers.
- **Postgres / SQLite MCP**: Direct schema inspection, migration execution, and verification of zero-fabrication constraints.
- **Context7 MCP**: Grounding of API documentation and library signatures.

---

## 5. Strict Anti-Plagiarism & Integrity Policy

In strict conformance with NASA Space Apps rules and project directives:
1. **Original Logic Mandate**:
   All core application logic—including data ingestion parsers, the Pint-based SI unit normalization engine, the comparison equivalence engine, the scientific entity extractor, the hybrid RRF search algorithm, and the Next.js visual components—must be original, purpose-built implementations for "Flame in Freefall".
2. **No Code Scraping / Facades**:
   No code may be lifted from existing open-source repositories for business logic. Pre-built third-party microservices, dummy mocking facades, or hardcoded fake data generators are strictly prohibited.
3. **Licensed Tooling Usage**:
   Standard, properly licensed open-source libraries (e.g. FastAPI, SQLAlchemy, Pint, FastEmbed, Next.js, Tailwind CSS) are used in accordance with their respective permissive licenses (MIT, Apache 2.0, BSD).
