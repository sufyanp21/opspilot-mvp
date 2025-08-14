from __future__ import annotations

from datetime import datetime, timezone


def age_in_hours(created_at: datetime, now: datetime | None = None) -> float:
    if now is None:
        now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    delta = now - created_at
    return delta.total_seconds() / 3600.0


def compute_age_bucket(created_at: datetime, now: datetime | None = None) -> str:
    hours = age_in_hours(created_at, now)
    if hours < 1:
        return "lt_1h"
    if hours < 4:
        return "h1_4h"
    if hours < 24:
        return "h4_24h"
    if hours < 24 * 3:
        return "d1_3d"
    return "gt_3d"


