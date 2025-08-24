from __future__ import annotations

from typing import Any, Dict, Tuple


def classify_root_cause(exc: Dict[str, Any]) -> Tuple[str, float, Dict[str, Any] | None]:
    """Rule-based root-cause classification and suggested resolution.

    Returns: (root_cause, confidence, suggested_resolution | None)
    """
    etype = str(exc.get("type", "")).upper()
    cluster = str(exc.get("cluster", "") or "")
    details = exc.get("details") or {}

    if etype == "MISSING_EXTERNAL":
        return (
            "External record missing",
            0.8,
            {"action": "requeue_external_fetch", "confidence": 0.6},
        )
    if etype == "MISSING_INTERNAL":
        return (
            "Internal record missing",
            0.8,
            {"action": "request_internal_republish", "confidence": 0.6},
        )
    if etype == "FIELD_MISMATCH":
        # Heuristics for quantity/price based on cluster/product codes
        if any(k in cluster for k in ("ES", "NQ", "CL", "GC")):
            return (
                "Quantity tolerance exceeded",
                0.7,
                {"action": "auto_clear_if_within_1_tick", "confidence": 0.5},
            )
        return (
            "Price tick deviation",
            0.7,
            {"action": "auto_clear_if_within_fx_rounding", "confidence": 0.5},
        )
    if "expiry" in cluster.lower():
        return ("Contract expiration mismatch", 0.7, None)

    return ("General discrepancy", 0.5, None)


