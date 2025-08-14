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
