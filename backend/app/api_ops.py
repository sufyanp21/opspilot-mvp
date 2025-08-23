from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from .security.auth import require_roles, User


router = APIRouter(prefix="/ops", tags=["ops"]) 


@router.get("/sources")
def list_sources(user: User = Depends(require_roles("analyst", "admin"))):
    now = datetime.now(timezone.utc)
    return {
        "items": [
            {
                "source_id": "sftp-cme",
                "kind": "sftp",
                "last_run": (now - timedelta(minutes=42)).isoformat(),
                "last_file": "positions_20250812.csv",
                "next_schedule": (now + timedelta(minutes=18)).isoformat(),
                "status": "ok",
            },
            {
                "source_id": "s3-internal",
                "kind": "s3",
                "last_run": (now - timedelta(minutes=5)).isoformat(),
                "last_file": "trades_20250812.csv",
                "next_schedule": (now + timedelta(minutes=55)).isoformat(),
                "status": "ok",
            },
        ]
    }


@router.get("/schedules")
def list_schedules(user: User = Depends(require_roles("analyst", "admin"))):
    return {"items": [{"source_id": "sftp-cme", "cron": "*/30 * * * *"}, {"source_id": "s3-internal", "cron": "0 * * * *"}]}


@router.post("/trigger/{source_id}")
def trigger_source(source_id: str, user: User = Depends(require_roles("admin"))):
    return {"ok": True, "source_id": source_id, "triggered": True}


@router.post("/webhooks/alert")
def webhook_alert(payload: Dict[str, Any]):
    # unauthenticated stub for external alert receivers; no-op
    return {"ok": True}


