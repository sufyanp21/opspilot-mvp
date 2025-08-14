from __future__ import annotations

import io
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse, StreamingResponse
from prometheus_client import CollectorRegistry, Counter, generate_latest, CONTENT_TYPE_LATEST

from .schemas_cdm import Trade
from .ingestion import csv as csv_ing
from .recon.engine import reconcile_trades
from .reports.exceptions_csv import exceptions_to_csv
from .audit.logger import AuditLogger
from .risk.span import diff_span_params, summarize_span_changes
from .ml.predict import load_training_data, train_model, predict_breaks
from .margin.impact import compute_margin_impact
from .margin.positions import compute_im_vm_from_positions
from .reports.regulatory import validate_regulatory, build_reg_pack
from .recon.cluster import cluster_exceptions
from .recon.nway import reconcile_nway
from .db import init_db, get_session_optional, AuditHeader
from .observability import setup_tracing
from .demo.orchestrator import run_demo
from .settings import settings
from .api_auth import router as auth_router
from .api_breaks import router as breaks_router
from .api_runs import router as runs_router
from .security.auth import get_current_user, require_roles, User
from .security.rate_limit import path_scoped_rate_limit
from .audit.log_helper import auditlog
from .run_utils import summarize_exceptions, count_auto_cleared


TMP_DIR = Path(os.getenv("TMP_DIR", "/tmp/opspilot"))
TMP_DIR.mkdir(parents=True, exist_ok=True)

AI_ENABLED = os.getenv("AI_ENABLED", "false").lower() == "true"

app = FastAPI(title="OpsPilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limit auth and upload endpoints
app.middleware("http")(path_scoped_rate_limit({"/auth", "/upload"}, settings.rate_limit_auth_per_minute))

audit_logger = AuditLogger(base_dir=TMP_DIR / "audit")
MODEL_CACHE = {"predict": None}

registry = CollectorRegistry()
REQ_COUNTER = Counter("requests_total", "Total API requests", ["endpoint"], registry=registry)
MATCHES_TOTAL = Counter("matches_total", "Total matched trades", registry=registry)
MISMATCHES_TOTAL = Counter("mismatches_total", "Total mismatched trades", registry=registry)
REG_PACKS_TOTAL = Counter("reg_packs_total", "Total regulatory packs generated", registry=registry)


@app.get("/health")
def health() -> Dict[str, Any]:
    REQ_COUNTER.labels(endpoint="health").inc()
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/upload")
async def upload(
    files: List[UploadFile] = File(...),
    tenant_id: Optional[str] = Form(None),
    force: Optional[bool] = Form(default=False),
    db=Depends(get_session_optional),
    user: User = Depends(require_roles("analyst", "admin")),
) -> Dict[str, Any]:
    REQ_COUNTER.labels(endpoint="upload").inc()
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    upload_id = str(uuid.uuid4())
    upload_dir = TMP_DIR / "uploads" / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_files: List[Dict[str, str]] = []
    for f in files:
        dest = upload_dir / f.filename
        content = await f.read()
        dest.write_bytes(content)
        # register in file registry (dedupe)
        try:
            reg = csv_ing.register_file(db, source="upload", filename=f.filename, content=content, force=bool(force))
            if reg.get("skipped"):
                continue
        except Exception:
            pass
        stored_files.append({"filename": f.filename, "path": str(dest)})

    audit_logger.write_event(
        action="upload",
        metadata={"upload_id": upload_id, "files": stored_files, "tenant_id": tenant_id},
    )
    # Persist audit header (optional if DB configured)
    if db is not None:
        try:
            db.add(AuditHeader(time=datetime.now(timezone.utc), action="upload", correlation_id=upload_id))
            db.commit()
            auditlog(db, action="file_ingested", user_id=user.user_id, actor_email=user.email, object_type="upload", object_id=upload_id, details={"files": [f["filename"] for f in stored_files]})
        except Exception:
            pass
    return {"upload_id": upload_id, "files": stored_files}


@app.post("/reconcile")
async def reconcile(
    internal_csv: UploadFile | None = File(default=None),
    external_csv: UploadFile | None = File(default=None),
    internal_path: Optional[str] = Form(default=None),
    external_path: Optional[str] = Form(default=None),
    db=Depends(get_session_optional),
    user: User = Depends(require_roles("analyst", "admin")),
) -> JSONResponse:
    REQ_COUNTER.labels(endpoint="reconcile").inc()
    # Load data from either uploaded files or provided paths
    def _df_from_upload(upload: UploadFile | None) -> Optional[pd.DataFrame]:
        if upload is None:
            return None
        content = upload.file.read()
        return pd.read_csv(io.BytesIO(content))

    df_internal: Optional[pd.DataFrame] = _df_from_upload(internal_csv)
    df_external: Optional[pd.DataFrame] = _df_from_upload(external_csv)

    if internal_path and df_internal is None:
        df_internal = pd.read_csv(internal_path)
    if external_path and df_external is None:
        df_external = pd.read_csv(external_path)

    if df_internal is None or df_external is None:
        raise HTTPException(status_code=400, detail="Provide internal/external CSV uploads or paths")

    # Validate + normalize to CDM-aligned schema
    internal_trades = csv_ing.parse_trade_csv(df_internal)
    external_trades = csv_ing.parse_trade_csv(df_external)

    result = reconcile_trades(internal_trades, external_trades, recon_config_path=settings.recon_config_path)

    audit_logger.write_event(
        action="reconcile",
        metadata={
            "summary": result["summary"],
            "exception_count": len(result.get("exceptions", [])),
        },
    )
    try:
        MATCHES_TOTAL.inc(result["summary"].get("matches", 0))
        MISMATCHES_TOTAL.inc(result["summary"].get("mismatches", 0))
    except Exception:
        pass
    if db is not None:
        try:
            db.add(AuditHeader(time=datetime.now(timezone.utc), action="reconcile", correlation_id=None))
            db.commit()
            auditlog(db, action="recon_completed", user_id=user.user_id, actor_email=user.email, object_type="recon", object_id=None, details=result.get("summary"))
        except Exception:
            pass
        # Optionally persist run summary if table exists
        try:
            from .models import ReconRun
            excs = result.get("exceptions", [])
            summary = result.get("summary", {})
            run = ReconRun(
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                matched=int(summary.get("matches", 0)),
                auto_tol=count_auto_cleared(excs),
                breaks_by_type=summarize_exceptions(excs),
                duration_ms=0,
                status="completed",
                error=None,
            )
            db.add(run)
            db.commit()
        except Exception:
            pass
    return JSONResponse(result)


@app.get("/reports/exception")
def report_exception(
    internal_path: str = Query(...),
    external_path: str = Query(...),
    user: User = Depends(require_roles("analyst", "admin")),
):
    REQ_COUNTER.labels(endpoint="report_exception").inc()
    df_internal = pd.read_csv(internal_path)
    df_external = pd.read_csv(external_path)
    internal_trades = csv_ing.parse_trade_csv(df_internal)
    external_trades = csv_ing.parse_trade_csv(df_external)
    result = reconcile_trades(internal_trades, external_trades)
    csv_bytes = exceptions_to_csv(result.get("exceptions", []))
    headers = {
        "Content-Disposition": f"attachment; filename=exceptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    }
    return StreamingResponse(io.BytesIO(csv_bytes), media_type="text/csv", headers=headers)


@app.post("/reconciliation/predictions")
async def reconciliation_predictions(candidates: List[Dict[str, Any]], user: User = Depends(require_roles("analyst", "admin"))) -> Dict[str, Any]:
    REQ_COUNTER.labels(endpoint="reconciliation_predictions").inc()
    # Train/load model (in-memory for demo)
    if MODEL_CACHE["predict"] is None:
        df = load_training_data(TMP_DIR / "training_breaks.csv")
        MODEL_CACHE["predict"] = train_model(df)
    preds = predict_breaks(MODEL_CACHE["predict"], candidates)
    audit_logger.write_event(action="predict_breaks", metadata={"count": len(preds)})
    return {"predictions": preds}


@app.get("/risk/changes")
def risk_changes(user: User = Depends(require_roles("analyst", "admin"))) -> Dict[str, Any]:
    REQ_COUNTER.labels(endpoint="risk_changes").inc()
    # Mock: return sample risk parameter deltas
    today = {
        "SPAN_SCANNING_RANGE": 15.0,
        "INTERCOMMODITY_CREDIT": 0.8,
        "DELTA_SCALER": 1.05,
    }
    yesterday = {"SPAN_SCANNING_RANGE": 14.5, "INTERCOMMODITY_CREDIT": 0.75, "DELTA_SCALER": 1.0}
    diff = diff_span_params(today, yesterday)
    return {
        "asOf": datetime.now(timezone.utc).date().isoformat(),
        "changes": [
            {"param": k, "old": v["old"], "new": v["new"], "delta": v["delta"]} for k, v in diff.items()
        ],
        "summary": summarize_span_changes(diff),
    }

@app.post("/margin/impact")
def margin_impact(payload: Dict[str, Any], user: User = Depends(require_roles("analyst", "admin"))) -> Dict[str, Any]:
    REQ_COUNTER.labels(endpoint="margin_impact").inc()
    unresolved = payload.get("exceptions", [])
    span_params = payload.get("span_params", {})
    impact = compute_margin_impact(unresolved, span_params)
    audit_logger.write_event(action="margin_impact", metadata={"items": len(impact.get("items", []))})
    return impact


@app.post("/margin/positions")
def margin_from_positions(payload: Dict[str, Any], user: User = Depends(require_roles("analyst", "admin"))) -> Dict[str, Any]:
    REQ_COUNTER.labels(endpoint="margin_positions").inc()
    positions = payload.get("positions", [])
    span_params = payload.get("span_params", {})
    out = compute_im_vm_from_positions(positions, span_params)
    audit_logger.write_event(action="margin_positions", metadata={"items": len(out.get("items", []))})
    return out


@app.post("/reports/regulatory/export")
def regulatory_export(payload: Dict[str, Any], user: User = Depends(require_roles("analyst", "admin"))):
    REQ_COUNTER.labels(endpoint="regulatory_export").inc()
    records = payload.get("records", [])
    lineage = payload.get("lineage", {})
    results = validate_regulatory(records)
    content = build_reg_pack(results, lineage)
    headers = {"Content-Disposition": "attachment; filename=reg_pack.zip"}
    audit_logger.write_event(action="reg_export", metadata={"records": len(records)})
    try:
        REG_PACKS_TOTAL.inc()
    except Exception:
        pass
    return StreamingResponse(io.BytesIO(content), media_type="application/zip", headers=headers)


@app.post("/reconcile/cluster")
def reconcile_cluster(payload: Dict[str, Any], user: User = Depends(require_roles("analyst", "admin"))) -> Dict[str, Any]:
    REQ_COUNTER.labels(endpoint="reconcile_cluster").inc()
    clusters = cluster_exceptions(payload.get("exceptions", []))
    audit_logger.write_event(action="cluster_exceptions", metadata={"clusters": len(clusters)})
    return {"clusters": clusters}


@app.post("/reconcile/nway")
def reconcile_n_way(payload: Dict[str, Any], user: User = Depends(require_roles("analyst", "admin"))) -> Dict[str, Any]:
    REQ_COUNTER.labels(endpoint="reconcile_n_way").inc()
    def to_trades(rows):
        return [Trade(**r) for r in rows]
    internal = to_trades(payload.get("internal", []))
    broker = to_trades(payload.get("broker", []))
    ccp = to_trades(payload.get("ccp", []))
    order = payload.get("authoritative_order", ["ccp", "broker", "internal"])
    tol = payload.get("tolerances", {"price": 0.0, "quantity": 0.0})
    result = reconcile_nway(internal, broker, ccp, order, tol)
    audit_logger.write_event(action="reconcile_nway", metadata={"matches": result.get("matches")})
    return result


@app.get("/metrics")
def metrics():
    return StreamingResponse(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
def on_startup():
    try:
        init_db()
    except Exception:
        pass
    try:
        setup_tracing(app)
    except Exception:
        pass
    # No return value for startup hook


@app.post("/demo/run")
def demo_run(user: User = Depends(require_roles("analyst", "admin"))) -> Dict[str, Any]:
    REQ_COUNTER.labels(endpoint="demo_run").inc()
    return run_demo(Path.cwd())


@app.post("/exceptions/bulk_resolve")
def exceptions_bulk_resolve(payload: Dict[str, Any], user: User = Depends(require_roles("analyst", "admin"))) -> Dict[str, Any]:
    REQ_COUNTER.labels(endpoint="exceptions_bulk_resolve").inc()
    trade_ids = payload.get("trade_ids", [])
    audit_logger.write_event(action="bulk_resolve", metadata={"count": len(trade_ids), "trade_ids": trade_ids})
    return {"resolved": len(trade_ids)}


# Routers
app.include_router(auth_router)
app.include_router(breaks_router)
app.include_router(runs_router)
