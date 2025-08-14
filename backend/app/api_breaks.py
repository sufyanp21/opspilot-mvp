from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .audit.log_helper import auditlog
from .db import get_session_optional
from .models import Break, BreakComment
from .security.auth import get_current_user, require_roles, User


router = APIRouter(prefix="/breaks", tags=["breaks"]) 


class BreakActionRequest(BaseModel):
    assigned_to: Optional[str] = None
    reason_code: Optional[str] = None
    note: Optional[str] = None


def _get_break(db: Session | None, break_id: int) -> Break:
    if db is None:
        # In environments without DB configured, behave as if not found
        raise HTTPException(status_code=404, detail="Break not found")
    brk = db.get(Break, break_id)
    if not brk:
        raise HTTPException(status_code=404, detail="Break not found")
    return brk


@router.post("/{break_id}/assign")
def assign_break(break_id: int, payload: BreakActionRequest, db=Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    brk = _get_break(db, break_id)
    brk.assigned_to = payload.assigned_to or user.email
    brk.status = "ASSIGNED"
    brk.updated_at = datetime.now(timezone.utc)
    if db is not None:
        db.add(brk)
        db.commit()
    auditlog(db, action="break_assign", user_id=user.user_id, actor_email=user.email, object_type="break", object_id=str(brk.id), details={"assigned_to": brk.assigned_to})
    return {"ok": True}


@router.post("/{break_id}/comment")
def comment_break(break_id: int, payload: BreakActionRequest, db=Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    brk = _get_break(db, break_id)
    c = BreakComment(break_id=brk.id, user_id=user.user_id or user.email, ts_utc=datetime.now(timezone.utc), text=payload.note or "")
    if db is not None:
        db.add(c)
        db.commit()
    auditlog(db, action="break_comment", user_id=user.user_id, actor_email=user.email, object_type="break", object_id=str(brk.id))
    return {"ok": True}


@router.post("/{break_id}/resolve")
def resolve_break(break_id: int, payload: BreakActionRequest, db=Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    brk = _get_break(db, break_id)
    brk.status = "RESOLVED"
    brk.resolved_at = datetime.now(timezone.utc)
    brk.reason_code = payload.reason_code
    brk.updated_at = datetime.now(timezone.utc)
    if db is not None:
        db.add(brk)
        db.commit()
    auditlog(db, action="break_resolve", user_id=user.user_id, actor_email=user.email, object_type="break", object_id=str(brk.id), details={"reason_code": brk.reason_code})
    return {"ok": True}


@router.post("/{break_id}/suppress")
def suppress_break(break_id: int, db=Depends(get_session_optional), user: User = Depends(require_roles("admin"))):
    brk = _get_break(db, break_id)
    brk.status = "SUPPRESSED"
    brk.updated_at = datetime.now(timezone.utc)
    if db is not None:
        db.add(brk)
        db.commit()
    auditlog(db, action="break_suppress", user_id=user.user_id, actor_email=user.email, object_type="break", object_id=str(brk.id))
    return {"ok": True}


@router.post("/{break_id}/unsuppress")
def unsuppress_break(break_id: int, db=Depends(get_session_optional), user: User = Depends(require_roles("admin"))):
    brk = _get_break(db, break_id)
    brk.status = "NEW"
    brk.updated_at = datetime.now(timezone.utc)
    if db is not None:
        db.add(brk)
        db.commit()
    auditlog(db, action="break_unsuppress", user_id=user.user_id, actor_email=user.email, object_type="break", object_id=str(brk.id))
    return {"ok": True}


@router.post("/{break_id}/reopen")
def reopen_break(break_id: int, db=Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    brk = _get_break(db, break_id)
    brk.status = "ASSIGNED" if brk.assigned_to else "NEW"
    brk.updated_at = datetime.now(timezone.utc)
    brk.resolved_at = None
    if db is not None:
        db.add(brk)
        db.commit()
    auditlog(db, action="break_reopen", user_id=user.user_id, actor_email=user.email, object_type="break", object_id=str(brk.id))
    return {"ok": True}


