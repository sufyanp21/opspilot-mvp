from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .demo.orchestrator import run_demo
from .security.auth import require_roles, User
from .db import get_session_optional
from .models import ReconRun, AnomalyLog, Break
from .anomaly_detection import MetricWindow, detect_pct_delta, get_window, detect_zscore
from .root_cause import classify_root_cause


router = APIRouter(prefix="/demo", tags=["demo"]) 


@router.post("/auto")
def demo_auto(user: User = Depends(require_roles("analyst", "admin")), db: Session | None = Depends(get_session_optional)) -> Dict[str, Any]:
    """Run a one-click automated demo: synthesize/locate data and produce KPIs + sample exceptions.

    Returns a compact payload suitable for KPI cards and a preview table.
    """
    base = Path.cwd()
    result = run_demo(base)
    if "error" in result:
        return {
            "matchRate": 0.0,
            "otcMatchRate": 0.0,
            "exceptionsSample": [],
            "spanDiffSummary": [],
            "runId": datetime.now(timezone.utc).isoformat(),
            "featureToggles": {"predictions": False},
            "error": result["error"],
        }

    k = result.get("kpis", {})
    exc: List[Dict[str, Any]] = result.get("exceptions", [])[:10]
    span = result.get("span", {})
    total = (k.get("matches", 0) or 0) + (k.get("mismatches", 0) or 0) + (k.get("missing_internal", 0) or 0) + (k.get("missing_external", 0) or 0)
    match_rate = (k.get("matches", 0) / total) if total else 0.0

    payload = {
        "matchRate": round(match_rate, 4),
        "otcMatchRate": 0.0,  # placeholder until OTC synthesis lands
        "exceptionsSample": exc,
        "spanDiffSummary": span,
        "runId": datetime.now(timezone.utc).isoformat(),
        "featureToggles": {"predictions": False},
    }

    # Seed a ReconRun row for Run History if DB is configured
    if db is not None:
        try:
            rr = ReconRun(
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                source_set="demo-auto",
                matched=int(k.get("matches", 0) or 0),
                auto_tol=0,
                breaks_by_type={"FIELD_MISMATCH": len([e for e in exc if e.get("type") == "FIELD_MISMATCH"]), "MISSING_EXTERNAL": len([e for e in exc if e.get("type") == "MISSING_EXTERNAL"])},
                duration_ms=500,
                status="completed",
                error=None,
            )
            db.add(rr)
            db.commit()
        except Exception:
            pass

    # Basic anomaly: SPAN parameter delta threshold
    if db is not None and span:
        try:
            for key, obj in span.items():
                old_v = float(obj.get("old", 0))
                new_v = float(obj.get("new", 0))
                alert = detect_pct_delta(f"SPAN_{key}", old_v, new_v, pct_threshold=0.05)
                if alert.get("anomaly"):
                    db.add(AnomalyLog(
                        ts_utc=datetime.now(timezone.utc),
                        metric=alert["metric"],
                        value=alert["value"],
                        threshold=alert["threshold"],
                        anomaly_type=str(alert["anomaly_type"]),
                        run_id="DEMO_RUN_1",
                    ))
            db.commit()
        except Exception:
            pass

    # Match rate and exception count anomaly using rolling z-score (demo-only)
    try:
        mr_win = get_window("match_rate")
        mr = float(payload.get("matchRate", 0.0))
        mr_win.add(mr)
        mr_alert = detect_zscore(mr_win, mr, z_threshold=2.5)
        if db is not None and mr_alert.get("anomaly"):
            db.add(AnomalyLog(ts_utc=datetime.now(timezone.utc), metric=mr_alert["metric"], value={"value": mr}, threshold=mr_alert["threshold"], anomaly_type=str(mr_alert["anomaly_type"]), run_id="DEMO_RUN_1"))

        exc_win = get_window("exceptions_count")
        exc_cnt = int(len(exc))
        exc_win.add(exc_cnt)
        exc_alert = detect_zscore(exc_win, float(exc_cnt), z_threshold=2.5)
        if db is not None and exc_alert.get("anomaly"):
            db.add(AnomalyLog(ts_utc=datetime.now(timezone.utc), metric=exc_alert["metric"], value={"value": exc_cnt}, threshold=exc_alert["threshold"], anomaly_type=str(exc_alert["anomaly_type"]), run_id="DEMO_RUN_1"))
        if db is not None:
            db.commit()
    except Exception:
        pass

    # Persist exception sample as Break rows for Exceptions UI
    if db is not None and exc:
        try:
            now = datetime.now(timezone.utc)
            for e in exc:
                rc, conf, suggestion = classify_root_cause(e)
                br = Break(
                    run_id="DEMO_RUN_1",
                    type=str(e.get("type", "FIELD_MISMATCH")),
                    status="OPEN",
                    severity=str(e.get("severity", "MEDIUM")),
                    assigned_to=None,
                    created_at=now,
                    updated_at=now,
                    resolved_at=None,
                    reason_code=rc,
                    notes={"confidence": conf, "suggested_resolution": suggestion, **(e.get("details") or {})},
                    lineage={"trade_id": e.get("trade_id"), "cluster": e.get("cluster")},
                )
                db.add(br)
            db.commit()
        except Exception:
            pass

    return payload


