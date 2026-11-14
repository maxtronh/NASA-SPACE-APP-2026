# NASA SPACE APP 2026 - "FLAME IN FREEFALL" CODEBASE PLAN

## Project Overview
Scientific intelligence platform for NASA microgravity combustion research. FastAPI backend + Next.js 15 frontend.

---

## 📁 PROJECT STRUCTURE

```
backend/          # FastAPI Python Backend
  app/main.py     # App entry point, lifecycle, CORS, routers
  app/core/config.py  # Settings (DATABASE_URL, CORS, ENABLE_AUTO_SEED)
  app/core/gravity.py # Physics calculations
  app/db/session.py # DB init, pgvector, SQLite fallback
  app/services/seed_data.py  # NASA data seeding on startup
  app/api/v1/router.py      # Versioned API routes
  pyproject.toml    # Project config, dependencies
  Dockerfile        # Backend container
  alembic/          # DB migrations

frontend/         # Next.js 15 Frontend
  src/app/          # App router pages (dashboard, analytics, etc.)
  src/components/   # React components (Navbar, Chart, etc.)
  src/lib/api.ts    # API client (base: /api/v1)
  src/types/index.ts# TypeScript types
  package.json      # Dependencies (React 19, Tailwind, Plotly)
  tailwind.config.js# Styling config
  Dockerfile        # Frontend container

docker-compose.yml    # Full-stack: DB + Backend + Frontend
scripts/          # ingest_nasa_data.py, validate_provenance.py
notebooks/        # Jupyter demos
tests/            # E2E tests (tier1-tier4)
docs/             # PROJECT.md, IMPLEMENTATION_PLAN.md
README.md         # Project overview
```

---

## 🏗️ BACKEND (FastAPI)

### Tech Stack
- FastAPI + SQLAlchemy 2.x + pgvector
- PostgreSQL 16 (primary), SQLite (fallback via aiosqlite)
- Pydantic v2 for validation
- FastSettings for config
- uvicorn server

### Key Files
- `app/main.py` - Lifespan: init DB + seed data if empty. CORS middleware. Router inclusion.
- `app/core/config.py` - Settings from env vars (DATABASE_URL, CORS_ORIGINS, ENABLE_AUTO_SEED)
- `app/core/gravity.py` - Microgravity combustion calculations
- `app/db/session.py` - init_db(), get_db_engines(), check_db_health()
- `app/services/seed_data.py` - seed_database_if_empty() - authentic NASA records

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | DB health check |
| GET | `/` | Root status + version |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |
| GET | `/api/v1/...` | Versioned API |

### CORS
- Defaults allow: localhost:3000, localhost:8000, 127.0.0.1
- Configurable via CORS_ORIGINS env var

### Database
- PostgreSQL + pgvector for vector similarity
- SQLite fallback for development
- Alembic for migrations (alembic.ini)

---

## 🌐 FRONTEND (Next.js 15)

### Tech Stack
- Next.js 15 (App Router)
- React 19 + TypeScript
- Tailwind CSS 3 + tailwind-merge
- Plotly.js-dist-min + Recharts
- Lucide React icons

### Key Pages
- `/` - Landing/dashboard page
- `/app/analytics/page.tsx` - Analytics
- `/app/intelligence/page.tsx` - Intelligence insights
- `/app/investigations/page.tsx` - Research investigations
- `/app/compare/page.tsx` - Comparative analysis
- `/app/generative-artifacts/page.tsx` - Generative art

### Key Components
- `Navbar.tsx` - Top navigation
- `Footer.tsx` - Page footer
- `ScientificChart.tsx` - Data visualization
- `ProvenanceCard.tsx` - Data origin info
- `GenerativeArtifacts.tsx` - AI-generated visuals

### API Integration
- `src/lib/api.ts` - Fetch from `http://localhost:8000/api/v1`
- Environment: `NEXT_PUBLIC_API_URL`
- Auto-seeded NASA data flows backend→frontend

### Styling
- Tailwind utility-first
- Custom config in `tailwind.config.js`
- Global styles in `globals.css`

---

## 🐳 DOCKER DEPLOYMENT

### Services (docker-compose.yml)
1. **db** - `pgvector/pgvector:pg16` on port 5432
2. **backend** - FastAPI on port 8000, depends on db
3. **frontend** - Next.js on port 3000, depends on backend

### Networks
- `flame_net` (bridge network)
- Volume: `pg_data` for PostgreSQL persistence

### URLs
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### Env Vars (backend .env)
```
DATABASE_URL=postgresql+psycopg://flame_user:flame_secure_pass@localhost:5432/flame_freefall
CORS_ORIGINS=["http://localhost:3000"]
ENABLE_AUTO_SEED=true
ENVIRONMENT=development
```

### Frontend Env
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 🚀 DEVELOPMENT WORKFLOW

### Backend (manual)
```powershell
cd backend
pip install -e .
uvicorn app.main:app --reload     # http://localhost:8000
```

### Frontend (manual)
```powershell
cd frontend
npm install           # first time
npm run dev           # http://localhost:3000 (auto-reload)
```

### With Docker (recommended)
```powershell
cd c:\dev\NASA-SPACE-APP-2026
docker-compose up -d    # Start all services
# Services:
#   - flame_db: PostgreSQL 16 + pgvector
#   - flame_backend: FastAPI on :8000
#   - flame_frontend: Next.js on :3000
docker-compose down     # Stop all
```

### Testing
```powershell
pytest tests/           # Backend tests
# E2E: tests/e2e/test_tier1_feature_coverage.py, etc.
```

---

## 📋 QUICK START CHECKLIST

- [ ] `docker-compose up -d` (recommended) OR install PostgreSQL + backend deps
- [ ] `cd frontend && npm install && npm run dev`
- [ ] Visit `http://localhost:3000` in browser
- [ ] API docs: `http://localhost:8000/docs`
- [ ] Health check: `http://localhost:8000/health`
- [ ] Seed data auto-initializes on backend start (ENABLE_AUTO_SEED=true)

---
*Complete codebase plan for NASA Space App 2026 - "Flame in Freefall"*