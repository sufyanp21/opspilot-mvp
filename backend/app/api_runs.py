from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .db import get_session_optional
from .models import ReconRun
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


@router.post("/export/exceptions")
def export_exceptions(payload: Dict[str, Any], user: User = Depends(require_roles("analyst", "admin"))):
    exceptions = payload.get("exceptions", [])
    content = exceptions_to_csv(exceptions)
    headers = {"Content-Disposition": "attachment; filename=exceptions.csv"}
    return StreamingResponse(io.BytesIO(content), media_type="text/csv", headers=headers)


