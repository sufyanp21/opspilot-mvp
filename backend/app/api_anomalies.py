from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .db import get_session_optional
from .models import AnomalyLog
from .security.auth import require_roles, User


router = APIRouter(prefix="/anomalies", tags=["anomalies"]) 


@router.get("/recent")
def get_recent_anomalies(
    hours: int = Query(24, ge=1, le=168),
    db: Session | None = Depends(get_session_optional),
    user: User = Depends(require_roles("analyst", "admin")),
):
    if db is None:
        return {"items": []}
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = db.query(AnomalyLog).filter(AnomalyLog.ts_utc >= since).order_by(AnomalyLog.id.desc()).all()
    return {"items": [
        {
            "id": r.id,
            "ts": r.ts_utc.isoformat(),
            "metric": r.metric,
            "value": r.value,
            "threshold": r.threshold,
            "anomaly_type": r.anomaly_type,
            "run_id": r.run_id,
        }
        for r in rows
    ]}


