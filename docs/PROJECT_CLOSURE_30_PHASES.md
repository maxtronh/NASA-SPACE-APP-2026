# Project Closure Roadmap — 30 Phases

## Purpose and scope

This roadmap defines a measurable path from the current M9 implementation to a release-ready project. These are closure and verification phases, not 30 speculative feature additions. The proposed M8/E-01–E-25 research backlog remains deferred unless it is separately prioritized.

The current NASA Eyes (JPL) frontend change is part of the UI acceptance work: `/nasa-eyes` is the primary route and `/milky-way` redirects to it. The NASA Eyes iframe is an external service, not a local NASA telemetry feed.

## Phases and exit gates

| Phase | Focus | Exit gate |
|---:|---|---|
| 1 | Freeze the baseline | Record the commit, branch, environment, and current worktree changes; do not overwrite or commit unapproved work. |
| 2 | Reconcile project scope | Align README, `PROJECT.md`, task tracking, and milestone claims with the capabilities actually present. |
| 3 | Configuration inventory | Document required environment variables, defaults, and startup behavior without exposing credentials. |
| 4 | Database migration audit | Verify Alembic head, fresh-database upgrade, and schema consistency. |
| 5 | Database dialect parity | Run core repository tests on SQLite and PostgreSQL where supported; document intentional differences. |
| 6 | NASA data provenance audit | Trace representative records to valid NASA sources and verify checksums, timestamps, and null preservation. |
| 7 | Ingestion replay and recovery | Prove ingestion is idempotent and can recover from network, rate-limit, and partial-write failures. |
| 8 | API contract audit | Compare OpenAPI, Pydantic schemas, frontend types, and documented request/response shapes. |
| 9 | Health and readiness semantics | Ensure health reports distinguish process liveness, database availability, vector readiness, and optional services. |
| 10 | Exploration API validation | Verify bounds, enum handling, error responses, and deterministic physical calculations for exploration endpoints. |
| 11 | Scientific retrieval quality | Test hybrid retrieval, ranking stability, and source-backed citations against a reviewed query set. |
| 12 | Model fallback and abstention | Verify optional model failures are explicit, deterministic fallbacks are labeled, and unsupported claims abstain. |
| 13 | Streaming lifecycle | Exercise stream startup, cancellation, disconnect, backpressure, and resource cleanup. |
| 14 | Security review and threat model | Review authentication boundaries, input validation, SSRF, unsafe rendering, rate limits, and secret handling; resolve high-risk findings. |
| 15 | NASA Eyes-only frontend acceptance | Confirm the primary route shows only NASA Eyes (JPL), legacy links redirect, and no retired Milky Way/25-Faces controls remain. |
| 16 | Frontend failure states | Verify loading, backend-offline, embed-unavailable, and retry/direct-link experiences are clear and non-misleading. |
| 17 | Accessibility and responsive review | Check keyboard navigation, focus visibility, iframe title, contrast, zoom, and small-screen layout. |
| 18 | Frontend static quality | Run production build, lint, formatting, and TypeScript checks with recorded versions and results. |
| 19 | Backend unit coverage | Run focused unit suites for ingestion, schemas, physics, retrieval, and safety calculations. |
| 20 | Backend integration coverage | Exercise API/database integration against the supported test database configuration. |
| 21 | Critical user-journey E2E | Verify ingestion-to-citation, comparison, analytics, exploration, and NASA Eyes navigation end to end. |
| 22 | Adversarial scientific-data testing | Test missing values, malformed units, tampered hashes, invalid citations, and out-of-domain questions. |
| 23 | Performance baseline | Measure representative API and page-load latency, memory, and concurrent-request behavior; set thresholds from observed baselines. |
| 24 | Dependency and license audit | Review direct/transitive dependency advisories and licenses; resolve or document accepted risks. |
| 25 | Containerized deployment | Build and start the complete Compose stack, then verify service-to-service readiness and shutdown. |
| 26 | Secret and deployment hardening | Confirm secrets are externalized, production defaults are safe, and deployment configuration is reproducible. |
| 27 | Observability | Ensure structured logs expose actionable failures without sensitive payloads and document available health/metrics signals. |
| 28 | Backup and recovery runbook | Demonstrate a database backup/restore and document recovery steps and data-loss boundaries. |
| 29 | Demo and release documentation | Refresh setup steps, screenshots, known limitations, source attribution, and test evidence to match the shipped build. |
| 30 | Final release gate | Require all P0 gates green, review remaining risks, obtain owner approval, then tag/publish only when explicitly authorized. |

## Completion policy

- Mark a phase complete only with evidence (test output, review record, or reproducible command).
- Fix blockers at their source; do not mask failures with fallback success responses.
- Keep NASA-source attribution and the zero-fabrication/null-preservation rules intact.
- Do not treat the optional M8 research backlog as a release prerequisite.
- No commit, tag, or deployment is authorized by this roadmap alone.
