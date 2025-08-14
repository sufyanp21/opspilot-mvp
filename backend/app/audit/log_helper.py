from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..models import AuditLog


def auditlog(
    db: Session | None,
    *,
    action: str,
    user_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    object_type: Optional[str] = None,
    object_id: Optional[str] = None,
    details: Any = None,
) -> None:
    if db is None:
        return
    row = AuditLog(
        ts_utc=datetime.now(timezone.utc),
        user_id=user_id,
        actor_email=actor_email,
        action=action,
        object_type=object_type,
        object_id=object_id,
        details=details,
    )
    db.add(row)
    db.commit()


