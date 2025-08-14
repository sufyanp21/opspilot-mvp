from __future__ import annotations

from typing import Dict, List


def summarize_exceptions(exceptions: List[dict]) -> Dict[str, int]:
    by_type: Dict[str, int] = {}
    for e in exceptions:
        t = e.get("type", "UNKNOWN")
        by_type[t] = by_type.get(t, 0) + 1
    return by_type


def count_auto_cleared(exceptions: List[dict]) -> int:
    return sum(1 for e in exceptions if e.get("auto_cleared") is True)


