# Flame in Freefall — System Error & Mitigation Log
**Project**: CORTEXX Scientific Intelligence Platform ("Flame in Freefall")  
**Maintenance Policy**: All runtime errors, schema divergences, fallback activations, and external API anomalies must be recorded immediately.

---

## 1. Error Classification & Incident Matrix

| Incident ID | Timestamp (UTC) | Subsystem | Severity | Description / Symptom | Root Cause | Resolution / Mitigation Applied | Status |
|---|---|---|---|---|---|---|---|
| **ERR-001** | 2026-11-12T17:55:00Z | Python Runtime | Low | Running raw `python` invokes Microsoft Store alias error: *"Python was not found..."* | Windows 11 App Execution Alias mapped to inactive WindowsApps stub. | Created `.venv` with `uv venv .venv --python 3.12`. All scripts and services invoke `.venv\Scripts\python.exe` or `uv run`. | **RESOLVED** |
| **ERR-002** | 2026-11-12T17:56:00Z | Git VCS | Medium | `git config --global --list` returns `fatal: unable to read config file 'C:/Users/fix/.gitconfig'` | User profile has no global `.gitconfig` initialized. Unconfigured commits would fail. | Configured local repository credentials upon `git init`: `git config user.name "NASA Space Apps Team"` and `git config user.email "team@spaceapps.local"`. | **RESOLVED** |
| **ERR-003** | 2026-11-12T17:57:00Z | Container Infrastructure | Medium | `docker ps` returns named pipe error `//./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified` | Docker Desktop executable is installed but the background daemon process is not running. | Implemented dual-tier database abstraction: production services run on PostgreSQL 16 + pgvector container; local unit tests use SQLite + vector math fallback when daemon is offline. | **MITIGATED** |
| **ERR-004** | 2026-11-13T05:20:00Z | Dependencies | Low | `ModuleNotFoundError: No module named 'networkx'` & `h5py` | Advanced graph and HDF5 parsing modules required domain libraries not in initial base hatchling spec. | Installed via `uv pip install networkx h5py` and pinned in `backend/pyproject.toml`. | **RESOLVED** |
| **ERR-005** | 2026-11-13T05:22:00Z | Database / Ordering | Low | Tier 3 concordance test failed on non-deterministic row return order under SQLite fallback. | SQLite returns unordered SELECT queries in arbitrary physical page order. | Added deterministic `query.order_by(Investigation.slug.asc())` across investigation service queries. | **RESOLVED** |
| **ERR-006** | 2026-11-13T05:41:00Z | Frontend Build | Low | Next.js build transient `ENOENT` / lock on `.next/types/` during simultaneous rebuild. | Windows filesystem handle lock held by prior build worker. | Sequenced clean build process; verified 10/10 static routes generated cleanly. | **RESOLVED** |

---

## 2. Incident Detail Records

### Incident ERR-001: Windows Python Execution Alias
- **Observed Behavior**: Running `python` from PowerShell triggers:
  ```
  Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases.
  ```
- **Analysis**: Windows 11 ships with zero-byte application execution aliases in `C:\Users\<user>\AppData\Local\Microsoft\WindowsApps`. If CPython is installed via standalone installer or `uv` without checking the global PATH checkbox, Windows invokes the store stub.
- **Resolution**:
  - Virtual environment `.venv` created via `uv venv .venv --python 3.12`.
  - All command invocations must explicitly use `.venv\Scripts\python.exe` or `uv run`.

### Incident ERR-002: Missing Global Git Configuration
- **Observed Behavior**: Git inspection returned fatal missing config file on user root.
- **Analysis**: On fresh environments without prior git author configuration, any attempt to run `git commit` aborts with an identity prompt.
- **Resolution**:
  - Executed `git config user.name "NASA Space Apps Team"`
  - Executed `git config user.email "team@spaceapps.local"`
  - Verified local config persists inside `.git/config`.

### Incident ERR-003: Docker Daemon Offline at Startup
- **Observed Behavior**: `docker ps` cannot connect to Docker Desktop named pipe.
- **Analysis**: Docker Desktop 29.9.3 is installed on host, but WSL2 daemon is stopped to conserve host RAM (~1.57 GB free physical RAM under idle desktop load).
- **Resolution**:
  - Backend database layer utilizes SQLAlchemy ORM with multi-dialect support.
  - When Docker is active: connects to `postgresql+psycopg://postgres:postgres@localhost:5432/flame_in_freefall`.
  - When Docker is inactive: unit tests seamlessly use SQLite in-memory / local file with Python vector distance calculations.
  - Docker Desktop can be started on demand before containerized integration tests.

### Incident ERR-004: Missing Domain Libraries (NetworkX & HDF5)
- **Observed Behavior**: `ModuleNotFoundError` when importing `networkx` or `h5py` for Upgrades 23 and 07.
- **Analysis**: Base `pyproject.toml` only specified core web dependencies.
- **Resolution**: Installed `networkx>=3.0.0` and `h5py>=3.10.0` via `uv pip install` and added to project dependencies.

### Incident ERR-005: Non-Deterministic SQLite Result Ordering
- **Observed Behavior**: E2E Tier 3 cross-feature test asserted on first returned investigation slug; SQLite returned arbitrary row ordering.
- **Analysis**: Standard SQL without explicit `ORDER BY` does not guarantee deterministic order across distinct database engines.
- **Resolution**: Added `query.order_by(Investigation.slug.asc())` to ensure strict reproducible ordering.

### Incident ERR-006: Windows Filesystem File Lock on Next.js Build
- **Observed Behavior**: Next.js build failed with `ENOENT` on `.next/types/app/analytics/page.ts`.
- **Analysis**: Windows handles on `.next/cache` held open by prior background build process.
- **Resolution**: Sequenced build execution cleanly; confirmed 10/10 static routes generated successfully.
