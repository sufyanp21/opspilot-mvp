from __future__ import annotations

from typing import Dict, Any


def parse_span(file_path: str) -> Dict[str, Any]:
    """
    Stub SPAN parser. In dev, expect a simple key=value per line file.
    Example:
      SPAN_SCANNING_RANGE=15.0
      INTERCOMMODITY_CREDIT=0.8
    """
    params: Dict[str, Any] = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    try:
                        params[k.strip()] = float(v.strip())
                    except ValueError:
                        params[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return params


def diff_span_params(today: Dict[str, Any], yesterday: Dict[str, Any]):
    out: Dict[str, Dict[str, Any]] = {}
    keys = set(today.keys()) | set(yesterday.keys())
    for k in keys:
        old = yesterday.get(k)
        new = today.get(k)
        if old != new:
            try:
                delta = (new or 0) - (old or 0)
            except Exception:
                delta = None
            out[k] = {"old": old, "new": new, "delta": delta}
    return out


def summarize_span_changes(diff: Dict[str, Dict[str, Any]]) -> str:
    if not diff:
        return "No SPAN parameter changes detected."
    parts = []
    for k, v in diff.items():
        parts.append(f"{k}: {v['old']} → {v['new']} (Δ={v['delta']})")
    return "; ".join(parts)


