from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.breaks.sla import compute_age_bucket


def test_compute_age_buckets_boundaries():
    now = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert compute_age_bucket(now - timedelta(minutes=30), now) == "lt_1h"
    assert compute_age_bucket(now - timedelta(hours=2), now) == "h1_4h"
    assert compute_age_bucket(now - timedelta(hours=6), now) == "h4_24h"
    assert compute_age_bucket(now - timedelta(days=2), now) == "d1_3d"
    assert compute_age_bucket(now - timedelta(days=7), now) == "gt_3d"


