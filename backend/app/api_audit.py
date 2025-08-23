from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends

from .security.auth import require_roles, User


router = APIRouter(prefix="/audit", tags=["audit"]) 


@router.get("/{audit_id}")
def get_audit(audit_id: str, user: User = Depends(require_roles("analyst", "admin"))):
    # Stub: return minimal record
    return {"id": audit_id, "events": []}


@router.get("/lineage/{run_id}")
def get_lineage(run_id: str, user: User = Depends(require_roles("analyst", "admin"))):
    # Stub: return placeholder lineage
    return {"runId": run_id, "nodes": [], "edges": []}


