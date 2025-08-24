from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .security.auth import require_roles, User
from .db import get_session_optional
from .models import MappingTemplate


router = APIRouter(prefix="/ingestion", tags=["ingestion"]) 


@router.post("/files")
async def upload_file(file: UploadFile = File(...), user: User = Depends(require_roles("analyst", "admin"))) -> Dict[str, Any]:
    # Stub: accept multipart and pretend to register
    return {"ok": True, "filename": file.filename, "size": None}


@router.post("/records")
async def ingest_records(payload: List[Dict[str, Any]], user: User = Depends(require_roles("analyst", "admin"))):
    # Stub: accept JSON records and echo count
    return {"ok": True, "count": len(payload)}


class MappingPayload(BaseModel):
    source_id: str
    name: str
    mapping: Dict[str, Any]


@router.post("/mappings")
def save_mapping(payload: MappingPayload, db: Session | None = Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    if db is None:
        return {"ok": True, "id": 0, "note": "db not configured; dry-run"}
    now = datetime.now(timezone.utc)
    mt = MappingTemplate(source_id=payload.source_id, name=payload.name, version=1, mapping_json=payload.mapping, created_at=now, updated_at=now)
    db.add(mt)
    db.commit()
    db.refresh(mt)
    return {"ok": True, "id": mt.id}


@router.get("/mappings/{source_id}")
def get_mappings(source_id: str, db: Session | None = Depends(get_session_optional), user: User = Depends(require_roles("analyst", "admin"))):
    if db is None:
        return {"items": []}
    items = db.query(MappingTemplate).filter(MappingTemplate.source_id == source_id).order_by(MappingTemplate.id.desc()).all()
    return {"items": [
        {
            "id": it.id,
            "source_id": it.source_id,
            "name": it.name,
            "version": it.version,
            "mapping": it.mapping_json,
            "updated_at": it.updated_at.isoformat(),
        }
        for it in items
    ]}


