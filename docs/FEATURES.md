## OpsPilot v1 High-Moat Features

### Predictive Reconciliation
- Endpoint: `POST /reconciliation/predictions`
- Input: JSON array of candidate trades with `trade_id`, `quantity`, `price_dev`
- Output: predictions with probability, likely cause, suggested action
- Notes: sklearn Logistic Regression pipeline; synthetic training fallback

### Margin Impact View
- Endpoint: `POST /margin/impact`
- Input: `{ exceptions: [...], span_params: {...} }`
- Output: `{ total_im_delta, items: [{ trade_id, im_delta }] }`
- Notes: Simple IM delta approximation using SPAN scanning range and intercommodity credit

### Regulator-Ready Export
- Endpoint: `POST /reports/regulatory/export`
- Input: `{ records: [...], lineage: {...} }`
- Output: `application/zip` with CSV passes/fails per regime, lineage JSON, PDF summary placeholder

### Break Clustering & Bulk Resolution
- Endpoint: `POST /reconcile/cluster`
- Output: clusters with members
- Notes: cosine-normalized vectors with HDBSCAN when available (fallback to naive cosine threshold)

### N-way Reconciliation
- Endpoint: `POST /reconcile/nway`
- Input: `{ internal: [...], broker: [...], ccp: [...], authoritative_order: [...], tolerances: { price, quantity } }`
- Output: `{ matches, exceptions }`
  - UI: `/(recon)/nway` with authoritative badges in exception cards

### Demo Mode
- Frontend surfaces pages: Upload, Results, Risk Changes, Predicted Breaks, Reg Pack
- Wizard: `/(wizard)/demo` with steps (sources → tolerances → run) and Regulator Mode toggle

### Dataset & Demo Mode
- Synthetic but structurally authentic sample data under `sample_data/`:
  - `cme_positions_20250812.csv` (with currency/expiry anomalies)
  - `lch_trades_20250812.xml` (FpML 5.x IRS sample with mismatches)
  - `internal_trades.csv` (intentional quantity/price mismatches)
  - `cme_span_20250812.csv` (SPAN with inflated BTC scan)
- Demo wizard can auto-ingest these for a full end-to-end run

### Observability & Audit Enhancements
- Audit JSONL with hash-chain, correlation IDs supported
- Prometheus `/metrics` and OpenTelemetry FastAPI instrumentation (console exporter in dev)


