from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .security.auth import require_roles, User
from .db import get_session_optional
from .models import Break


router = APIRouter(prefix="/exceptions", tags=["exceptions"]) 


@router.get("")
def list_exceptions(limit: int = Query(50, ge=1, le=200), db: Session | None = Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    if db is None:
        return {"items": [], "total": 0}
    rows = db.query(Break).order_by(Break.created_at.desc()).limit(limit).all()
    items = [
        {
            "id": str(r.id),
            "status": r.status,
            "counterparty": None,
            "cluster": r.lineage.get("cluster") if isinstance(r.lineage, dict) else None,
            "sla_due_at": None,
            "description": r.type,
        }
        for r in rows
    ]
    return {"items": items, "total": len(items)}


@router.patch("/{exception_id}")
def update_exception(exception_id: str, payload: Dict[str, Any], user: User = Depends(require_roles("analyst", "admin"))):
    # Stub: pretend to update
    return {"ok": True, "id": exception_id, "changes": payload}


