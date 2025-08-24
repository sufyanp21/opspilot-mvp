from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .db import get_session_optional
from .models import ReconRun
from .models import PredictionBreak
from .security.auth import require_roles, User
from .reports.exceptions_csv import exceptions_to_csv
import io


router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/")
def list_runs(limit: int = Query(50, ge=1, le=500), db: Session | None = Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    if db is None:
        return {"items": [], "total": 0}
    items = db.query(ReconRun).order_by(ReconRun.id.desc()).limit(limit).all()
    out = [
        {
            "id": r.id,
            "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "matched": r.matched,
            "auto_tol": r.auto_tol,
            "breaks_by_type": r.breaks_by_type,
            "duration_ms": r.duration_ms,
            "status": r.status,
            "error": r.error,
        }
        for r in items
    ]
    return {"items": out, "total": len(out)}


@router.get("/{run_id}")
def get_run(run_id: str, db: Session | None = Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    if db is None:
        return {"id": run_id, "status": "completed", "matched": 0, "breaks_by_type": {}}
    r = db.get(ReconRun, int(run_id)) if run_id.isdigit() else None
    if not r:
        return {"id": run_id, "status": "unknown"}
    return {
        "id": r.id,
        "started_at": r.started_at.isoformat(),
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "matched": r.matched,
        "auto_tol": r.auto_tol,
        "breaks_by_type": r.breaks_by_type,
        "duration_ms": r.duration_ms,
        "status": r.status,
        "error": r.error,
    }


@router.get("/{run_id}/results")
def get_run_results(run_id: str, user: User = Depends(require_roles("analyst", "admin"))):
    # Stub: return minimal structure for UI wiring
    return {
        "runId": run_id,
        "kpis": {"matches": 0, "mismatches": 0, "missing_internal": 0, "missing_external": 0},
        "exceptions": [],
    }


@router.get("/{run_id}/predictions")
def get_run_predictions(run_id: str, db: Session | None = Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    if db is None:
        # synthesize small list for demo
        items = []
        for i in range(1, 11):
            prob = 0.1 * (i % 5)
            risk = "high" if prob >= 0.7 else ("med" if prob >= 0.4 else "low")
            items.append({
                "record_id": f"R{i}",
                "probability": prob,
                "risk": risk,
                "explanation": {"top": ["Price deviation", "Counterparty break rate"]},
            })
        return {"items": items}
    rows = db.query(PredictionBreak).filter(PredictionBreak.run_id == run_id).all()
    out = []
    for r in rows:
        prob = float(r.p_break) / 10000.0 if r.p_break is not None else 0.0
        risk = "high" if prob >= 0.7 else ("med" if prob >= 0.4 else "low")
        out.append({
            "record_id": r.record_id,
            "probability": prob,
            "risk": risk,
            "explanation": r.explanation_top or {},
        })
    return {"items": out}

@router.post("/export/exceptions")
def export_exceptions(payload: Dict[str, Any], user: User = Depends(require_roles("analyst", "admin"))):
    exceptions = payload.get("exceptions", [])
    content = exceptions_to_csv(exceptions)
    headers = {"Content-Disposition": "attachment; filename=exceptions.csv"}
    return StreamingResponse(io.BytesIO(content), media_type="text/csv", headers=headers)


