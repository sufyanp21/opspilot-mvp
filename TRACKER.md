# OpsPilot MVP Hardening & Pilot‑Ready Build – Workplan Tracker

This file tracks the implementation status for the hardening plan. Update as tasks complete, linking PRs.

## Branches
- feat/p0-security-audit – Security, Auth/RBAC, Audit Trail, Breaks workflow

## Checklist

- [ ] 0) Project Rules baseline
  - [ ] Python 3.11+ ensured in runtime
  - [ ] FastAPI, SQLAlchemy, Alembic, Pydantic v2, Celery/Redis configured
  - [ ] 12‑factor config via ENV and `backend/app/settings.py`
  - [ ] Lint/format hooks (ruff, black) and ESLint/Prettier
  - [ ] Tests >80% for touched code

- [ ] 1) Tracked Workplan
  - [x] `TRACKER.md` added

- [ ] 2) Security & Access (P0)
  - [x] JWT auth endpoints: `POST /auth/login`, `POST /auth/refresh`
  - [x] RBAC roles: admin, analyst (basic)
  - [x] Auth dependencies added to non‑public endpoints
  - [x] CORS tightened to ENV allowlist
  - [ ] Secrets from ENV; remove hard‑coded keys
  - [x] Rate limiting on auth + upload endpoints
  - [x] Tests: auth success/deny, basic checks (refresh token uniqueness)

- [ ] 3) Immutable Audit Trail (P0)
  - [x] DB table `audit_log` with JSON details
  - [x] Helper `auditlog(action, object_type, object_id, details)`
  - [ ] Events logged: auth success/failure, ingestion, recon start/complete, break changes, config edits
  - [ ] Tests: audit rows written

- [ ] 4) Breaks/Exceptions Workflow (P0)
  - [x] Models: `breaks`, `break_comments`
  - [x] Endpoints: assign, comment, resolve, suppress, unsuppress, reopen
  - [ ] SLA helpers (age buckets)
  - [ ] Tests: state transitions + auth

- [ ] 5) Tolerances & Matching (P0/P1)
  - [x] Config loader for tolerances (`config_loader.py`) and legacy param support
  - [x] Exact/composite (preferred key with UTI/UPI), FIELD_MISMATCH w/ auto‑clear
  - [x] UTI/UPI preference implemented
  - [x] Unit tests for abs tolerance and UTI match
  - [x] Recon config path wired via ENV; API uses it

- [ ] 6) Performance (P1)
  - [ ] Pandas/Polars joins for compares; chunking
  - [ ] Batch DB writes, transactions, indexes on (run_id, status, type)
  - [ ] Benchmark: 100k/side < 5s (document)

- [ ] 7) Ingestion Resilience & Idempotency (P1)
  - [x] `file_registry` table; SHA‑256 dedupe; force flag on upload
  - [x] CSV schema validation; Excel helper
  - [x] SFTP processing stub + Celery task to process files; periodic poll via env `SFTP_LOCAL_DIRS`
  - [x] Tests: duplicate suppression; missing column handling

- [ ] 8) OTC MVP (P1)
  - [ ] Minimal OTC schema; FpML lite + CSV parser
  - [ ] Recon by UTI/composite; breaks
  - [ ] Fixtures + tests

- [ ] 9) Run History & Exports (P2)
  - [ ] `recon_runs` model/API/UI; CSV export

- [ ] 10) Frontend Enhancements (P1/P2)
  - [ ] Auth screens; role‑gated nav
  - [ ] Dashboard KPIs; Breaks queue; Break detail; Run history; Exports; Toasts

- [ ] 11) Config Versioning (P2)
  - [ ] `config_items` DB; admin endpoints; audit logs

- [ ] 12) DevEx & CI
  - [x] ruff/black/pre-commit config; GH Actions backend + frontend pipelines
  - [x] pyproject.toml with tool configs
  - [x] Slim Dockerfiles, non‑root users (backend/frontend Dockerfile.prod)
  - [x] README_new.md with ENV vars and quickstart

## PRs
- (link here as they are opened/merged)

## Benchmarks & Notes
- Perf target: 100k x 100k compare < 5s on laptop
- Tradeoffs considered and rationale:
  - TBD


