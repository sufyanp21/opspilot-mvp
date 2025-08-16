## OpsPilot Master Context (Cursor Chat Consolidation)

Authoring context for fast, consistent work in Cursor. This file captures the current architecture, environment conventions, known fixes, and operational guardrails distilled from our chat.

### Repository Overview
- Monorepo root: `MVP/`
- Primary backend (FastAPI): `backend/`
- Primary frontend (React + Vite): `apps/web/`
- Secondary legacy demo stack (keep isolated): `opspilot-mvp/` (do not mix with `apps/web`)
- Next.js sample module: `frontend/` (separate; not used for the Vite app)

### Operating Environment
- OS: Windows 10/11 (PowerShell)
- Python: 3.11+
- Node: Vite dev server
- Database: Postgres (via Alembic migrations)

### Critical Run Rules (Cursor + PowerShell)
- Do NOT run a bare `cd` in Cursor. Always chain commands in a subshell so the process doesn’t stall.
  - Backend (subshell): `(cd backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload)`
  - Frontend (subshell): `(cd apps/web; npm run dev)`
- Default networking: backend on `127.0.0.1:8000`, frontend on `localhost:5173` (Vite may auto-bump to 5174/5175 if busy)

### Backend (FastAPI) Summary
- Entry: `backend/app/main.py`
  - CORS uses `settings.allow_origins`
  - Basic rate limiting middleware
  - Routers include auth, exceptions, reconciliation, runs, span, margin, files
  - Non-public endpoints protected via `Depends(require_roles)`
  - Audit logging on sensitive flows (auth success/failure, upload, reconcile)
  - TMP_DIR set to `./tmp/opspilot` for Windows compatibility
- Config: `backend/app/settings.py` (Pydantic v2)
  - Loads `.env` via `SettingsConfigDict(env_file=".env")`
  - Includes `recon_config_path`
- Auth & RBAC: `backend/app/security/auth.py`
  - JWT create/verify; refresh issues fixed to ensure new tokens on refresh
- Recon engine: `backend/app/recon/engine.py`
  - Prefer UTI/UPI match, then trade_id/composite; tolerances (abs + pct)
- Ingestion & Idempotency: `backend/app/ingestion/csv.py`, `excel.py`, `sftp.py`
  - `register_file` with SHA256 dedupe and `force` flag
- Run history: `backend/app/api_runs.py` and helpers in `run_utils.py`
- Audit helpers: `backend/app/audit/log_helper.py` handles `db=None` gracefully
- Migrations: `backend/alembic/versions/*` (audit_log, breaks, break_comments, file_registry, recon_runs)

#### Backend: Common Commands (PowerShell subshell)
```powershell
(cd backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload)
```
Health check:
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing
```

### Frontend (React + Vite) Summary
- App root: `apps/web/`
- Entrypoint: `apps/web/src/main.tsx`
- Router: `apps/web/src/routes.tsx`
- Layout: `apps/web/src/components/layout/AppLayout.tsx`
- Auth guard: `apps/web/src/components/ProtectedRoute.tsx`
- API client: `apps/web/src/lib/api.ts` (Axios; injects `Authorization: Bearer` from `localStorage`)
- State: `apps/web/src/lib/store.ts` (Zustand; `user`, `isAuthenticated`, `logout`)
- React Query: `apps/web/src/lib/query.ts`
- UI: shadcn/ui components in `apps/web/src/components/ui/*`

#### Frontend Environment Variables
- Create `apps/web/.env` (or `.env.local`) with:
```
VITE_API_BASE=http://localhost:8000
```
- All API calls derive the base URL from `VITE_API_BASE`.

#### Frontend: Current Routes and Pages
`apps/web/src/routes.tsx` uses the professional UI pages and `AppLayout`:
- `Dashboard` (`/`)
- `Exceptions` (`/exceptions`)
- `Reconciliation` (`/reconciliation`)
- `FileUpload` (`/upload`)
- `SpanAnalysis` (`/span`)
- `OtcProcessing` (`/otc`)
- `AuditTrail` (`/audit`)
- `Login` (`/login`)
Routes are wrapped by `ProtectedRoute` where needed.

#### Frontend: Common Commands (PowerShell subshell)
```powershell
(cd apps/web; npm run dev)
```
If port conflicts occur, Vite may move to 5174/5175 automatically.

### Known Fixes Applied (from chat)
- Fixed duplicate `Alert` component export conflict
- Implemented `postJson`, `getJson`, `uploadFile` in `apps/web/src/lib/api.ts`
- Migrated routes to use new professional UI and `AppLayout`
- Deleted obsolete old UI files:
  - `apps/web/src/components/AppShell.tsx`
  - `apps/web/src/pages/Breaks.tsx`
  - `apps/web/src/pages/BreakDetail.tsx`
  - `apps/web/src/pages/Runs.tsx`
  - `apps/web/src/pages/Sources.tsx`
  - `apps/web/src/pages/Audit.tsx`
- Backend: fixed stray comma syntax error in route, JWT refresh uniqueness, audit logger `db=None` handling
- Backend: set TMP_DIR to `./tmp/opspilot` for Windows
- Tests: added test path configuration to avoid `ModuleNotFoundError: app`
- CI: stricter pytest flags; pre-commit `ruff` + `black`

### Common Issues and Fast Fixes
- Vite 404 on root: usually due to port conflict or wrong working dir
  - Kill stale processes: `Get-Process | ? { $_.ProcessName -like "*node*" -or $_.ProcessName -like "*vite*" } | Stop-Process -Force`
  - Ensure run from `apps/web`: `(cd apps/web; npm run dev)`
- Backend `ModuleNotFoundError: app`:
  - Ensure subshell runs from `backend` folder: `(cd backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload)`
- 401 loops in frontend:
  - Axios interceptor clears tokens and redirects to `/login`; confirm `VITE_API_BASE` and backend up
- `/health` times out:
  - Verify backend bind host is `127.0.0.1`; check firewall

### Security & Auth
- JWT access + refresh; role-based access: `admin`, `analyst`
- CORS allowlist via env
- Rate limiting on sensitive endpoints
- Secrets via environment variables only

### Reconciliation & Data
- Tolerances: absolute + percentage; match priority UTI/UPI → trade_id → composite
- Idempotent ingestion with `file_registry` and SHA256 dedupe; `force=true` to reprocess
- Run history persisted with summary metrics
- CSV/Excel parsers; SFTP processing task stubbed

### Networking Conventions
- Use `127.0.0.1` for backend host when testing locally
- Frontend Vite typically on `localhost:5173`

### Acceptance Criteria Snapshot (for quick QA)
1. `GET /health` returns `{status: "ok"}`
2. Login stores `opspilot_access` and redirects to `/`
3. `/demo` triggers backend demo action (if enabled)
4. `/exceptions` renders items; details navigable
5. API base derived from `VITE_API_BASE`

### Git Hygiene Notes
- Main branch may be named `main` (renamed from `master` previously)
- Force pushes were used to align remote history only when explicitly requested

### Deleted/Deprecated Files (do not reintroduce)
- `backend/app/ingestion/parsers/fpml_parser.py`
- `README.md`, `README_new.md`
- `demo_features.py`, `quick_demo.py`
- `backend/test_server.py`
- Old frontend pages/components listed above

### Quick Start (End-to-End)
1. Backend
```powershell
(cd backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload)
```
2. Frontend
```powershell
(cd apps/web; if (Test-Path .env) { Get-Content .env } else { "VITE_API_BASE=http://localhost:8000" | Out-File -Encoding utf8 .env }; npm run dev)
```
3. Open browser: `http://localhost:5173` (or next available port printed by Vite)

### Single‑Pass Frontend Change Policy
- Identify all impacted files first (routes, env, api client, layout, imports)
- Batch edits into one commit; avoid unrelated refactors
- Verify: points to correct backend; uses `VITE_API_BASE`; no imports from old UI; `npm run dev` and `npm run build` succeed



---

### Full Original OPSPILOT_CONTEXT.md (verbatim)

# OpsPilot Project Context (MVP + Demo)

This document captures the essential context you need to open new chats and continue work without reloading prior conversations. It centralizes architecture, modules, endpoints, data, env, run steps, and demo flow.

## Product Snapshot
- **Purpose**: AI-powered RegTech platform for derivatives post-trade automation
- **Modules**: Ingestion, reconciliation (ETD/OTC/N-way), exception management, SPAN/margin analysis, regulatory exports, audit/observability
- **Demo**: Local Docker Compose; investor-ready dashboard (Vite) + module pages (Next.js)

## Repository Map (key paths)
- **Backend (FastAPI)**: `backend/app/`
  - Entrypoint/API: `main.py`
  - Schemas (ISDA CDM-aligned subset): `schemas_cdm.py`
  - Ingestion adapters: `ingestion/{csv.py,sftp.py,api.py}`
  - Reconciliation: `recon/{engine.py,nway.py,cluster.py}`
  - Risk/SPAN: `risk/span.py`
  - Margin: `margin/{impact.py,positions.py}`
  - Reports: `reports/{exceptions_csv.py,regulatory.py}`
  - Audit: `audit/logger.py`
  - Observability: `observability.py`
  - Demo Orchestrator: `demo/orchestrator.py`
  - DB/ORM: `db.py`; Alembic in `backend/alembic/`
  - Celery tasks: `tasks.py`
- **Frontend Next.js (module pages)**: `frontend/`
- **Investor dashboard (Vite + Tailwind + shadcn)**: `apps/web/`
  - Vite config/alias: `apps/web/vite.config.ts` (`@` → `./src`)
  - Tailwind theme (CSS variables): `apps/web/tailwind.config.js`
  - Global tokens/styles: `apps/web/src/index.css`
  - App shell & routes: `apps/web/src/App.tsx`, entry `src/main.tsx`
  - UI primitives: `apps/web/src/components/ui/*`
- **Infra/docs**
  - Compose: `docker-compose.yml`
  - Terraform stubs: `infra/terraform/`
  - Architecture: `docs/architecture.md`
  - Features: `docs/FEATURES.md`
  - Security: `SECURITY_NOTES.md`
  - ADRs: `docs/ADR/ADR-00*.md`
  - Sample data: `sample_data/`

## Core Backend Endpoints
- Health: `GET /health`
- Upload: `POST /upload`
- Reconcile (ETD 2-way): `POST /reconcile` (CSV form-data or file paths)
- N-way Reconciliation: `POST /reconcile/nway`
- Exception Clustering: `POST /reconcile/cluster`
- Predictive breaks: `POST /reconciliation/predictions`
- Exception report (CSV): `GET /reports/exception`
- Regulatory pack (ZIP): `POST /reports/regulatory/export`
- Margin impact (exceptions): `POST /margin/impact`
- Margin from positions (IM/VM): `POST /margin/positions`
- SPAN Risk changes (mock): `GET /risk/changes`
- Demo Orchestrator: `POST /demo/run`
- Exceptions bulk resolve (audit): `POST /exceptions/bulk_resolve`
- Metrics (Prometheus): `GET /metrics`

## Recon Engine Highlights
- Matching by `trade_id`; composite-key fallback (product_code|account|price|quantity)
- Diffs, severity tags, cluster keys, root-cause text
- Auto-clear breaks within tolerance (price/quantity)
- N-way with authoritative order and tolerances (internal/broker/ccp)
- Clustering via HDBSCAN (fallback to cosine threshold)

## Risk & Margin
- SPAN parser stubs + daily diff summary
- Margin impact from exceptions (`margin/impact.py`)
- IM/VM from positions with SPAN-like params (`margin/positions.py`)

## Regulatory & Audit
- Regulator pack ZIP with per-regime CSV pass/fail, lineage JSON, PDF placeholder
- JSONL audit with hash-chain and correlation IDs; optional DB persistence (`AuditHeader`)

## Observability & Security
- Prometheus counters: requests, matches, mismatches, reg packs generated
- OpenTelemetry FastAPI instrumentation (console exporter in dev)
- Security defaults: CORS origins, env-based secrets, data minimization, retention

## Sample Data (single day)
- `sample_data/cme_positions_20250812.csv`
- `sample_data/lch_trades_20250812.xml` (FpML 5.x IRS)
- `sample_data/internal_trades.csv`
- `sample_data/cme_span_20250812.csv`
- Contains realistic anomalies: currency/expiry mismatches, missing trade, price/quantity diffs, inflated BTC SPAN scan

## Environment Variables (common)
- **Backend**
  - `CORS_ALLOW_ORIGINS`: `http://localhost:3000,http://localhost:5173`
  - `AI_ENABLED`: `false`
  - `OPENAI_API_KEY`: optional
  - `DATABASE_URL`: `postgresql+psycopg2://opspilot:opspilot@db:5432/opspilot`
  - `REDIS_URL`: `redis://redis:6379/0`
  - `USE_CELERY`: `false` (set `true` to run tasks async)
- **Frontend Next.js**: `NEXT_PUBLIC_API_BASE=http://localhost:8000`
- **Vite dashboard**: `VITE_API_BASE=http://localhost:8000`

## How to Run (local)
1) Build & start
```bash
docker-compose up --build
```

2) Open
- Backend API: http://localhost:8000/docs
- Vite dashboard (investor demo): http://localhost:5173
- Next.js app (module pages): http://localhost:3000
- Metrics: http://localhost:8000/metrics

3) Optional
- DB migration: `docker compose exec backend bash -lc "alembic upgrade head"`
- Celery worker: `docker compose up -d worker`

## Demo Flow (end-to-end)
- Vite dashboard → click "Run Demo" → triggers `POST /demo/run`
- Backend auto-ingests `sample_data/`, runs reconciliation, computes SPAN deltas → returns KPIs and exceptions for UI
- Next.js pages offer detailed flows: Upload, Reconciliation, Exceptions (clustering/bulk resolve), N-way, Risk, Reg Pack download, Margin Impact, Demo Wizard

## Frontend Notes (Vite + shadcn)
- `tailwind.config.js` defines CSS variables mapping (background, foreground, border, etc.) and animations; dark mode supported
- `index.css` sets CSS tokens under `@layer base` and applies `bg-background`/`text-foreground`
- UI primitives in `components/ui/*` are single-implementation shadcn components (no duplicate exports)
- Dev server hot-reload via compose mounts for `/app` and `/app/node_modules`

## Common Issues & Fixes
- **Tailwind error**: `bg-background` or `border-border` not found → ensure `apps/web/tailwind.config.js` includes CSS variable color mapping and `index.css` defines tokens; replace `border-border` with `border` or `border-gray-200` where needed
- **Duplicate exports / React redeclared** → ensure UI primitives have a single implementation and export set
- **CORS failures** → confirm `CORS_ALLOW_ORIGINS` includes the active frontend origin
- **Vite port mismatch** → keep `vite.config.ts` server.port aligned with compose (default 5173) or update compose to match

## Roadmap (post-demo)
- Generate OpenAPI TS client and replace manual fetches
- Wire Celery paths for heavy tasks and add status polling
- Expand SPAN/SPAN2 parsing; IM/VM per account/product; position-aware deltas
- Role-based demo auth; metric-driven dashboards; Regulator Mode toggle propagation

---
**This file is the canonical context for OpsPilot's MVP and demo. Update it when architecture/API/UI/infra change.**

