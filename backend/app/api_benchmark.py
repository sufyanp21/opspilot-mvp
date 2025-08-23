from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .db import get_session_optional
from .models import Break
from .security.auth import require_roles, User


router = APIRouter(prefix="/benchmark", tags=["benchmark"]) 


@router.get("/insights")
def get_insights(db: Session | None = Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    if db is None:
        return {"top_categories": [], "top_products": [], "avg_resolution_days": 0.0}
    rows = db.query(Break).all()
    by_type: Dict[str, int] = {}
    by_cluster: Dict[str, int] = {}
    total_resolved = 0
    total_resolved_days = 0.0
    for r in rows:
        by_type[r.type] = by_type.get(r.type, 0) + 1
        cl = r.lineage.get("cluster") if isinstance(r.lineage, dict) else None
        if cl:
            by_cluster[cl] = by_cluster.get(cl, 0) + 1
        if r.resolved_at:
            total_resolved += 1
            delta = r.resolved_at - r.created_at
            total_resolved_days += max(0.0, delta.total_seconds() / 86400.0)
    top_categories = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]
    top_products = sorted(by_cluster.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "top_categories": [{"category": k, "count": v} for k, v in top_categories],
        "top_products": [{"product": k, "count": v} for k, v in top_products],
        "avg_resolution_days": (total_resolved_days / total_resolved) if total_resolved else 0.0,
    }


@router.get("/insights/weekly")
def get_weekly_insights(db: Session | None = Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    if db is None:
        return {"weeks": []}
    now = datetime.now(timezone.utc)
    out = []
    for weeks_back in range(0, 4):
        start = (now - timedelta(days=now.weekday())) - timedelta(weeks=weeks_back)
        end = start + timedelta(days=7)
        rows = db.query(Break).filter(Break.created_at >= start, Break.created_at < end).all()
        out.append({
            "week_start": start.date().isoformat(),
            "total": len(rows),
        })
    return {"weeks": out}


@router.post("/recompute")
def recompute_insights(user: User = Depends(require_roles("admin"))):
    # Stub for scheduled recompute job; insights are computed on-demand in this MVP
    return {"ok": True, "recomputed": True}


