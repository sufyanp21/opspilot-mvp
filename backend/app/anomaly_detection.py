from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Deque, Dict, List, Tuple


@dataclass
class MetricWindow:
    name: str
    window_size: int = 20
    values: Deque[float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.values = deque(maxlen=self.window_size)

    def add(self, v: float) -> None:
        self.values.append(float(v))

    def mean_std(self) -> Tuple[float, float]:
        if not self.values:
            return 0.0, 0.0
        m = sum(self.values) / len(self.values)
        var = sum((x - m) ** 2 for x in self.values) / max(1, len(self.values) - 1)
        return m, var ** 0.5


def detect_zscore(metric: MetricWindow, current: float, z_threshold: float = 3.0) -> Dict:
    mean, std = metric.mean_std()
    z = 0.0 if std == 0 else (current - mean) / std
    is_anom = abs(z) >= z_threshold and len(metric.values) >= max(5, metric.window_size // 2)
    return {
        "metric": metric.name,
        "value": current,
        "threshold": {"type": "zscore", "z": z, "z_threshold": z_threshold, "mean": mean, "std": std},
        "anomaly": bool(is_anom),
        "anomaly_type": "high" if z > 0 else "low",
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def detect_pct_delta(name: str, old: float, new: float, pct_threshold: float) -> Dict:
    if old == 0:
        change = float('inf') if new != 0 else 0.0
    else:
        change = (new - old) / abs(old)
    is_anom = abs(change) >= pct_threshold
    return {
        "metric": name,
        "value": {"old": old, "new": new, "delta_pct": change},
        "threshold": {"type": "pct", "threshold": pct_threshold},
        "anomaly": bool(is_anom),
        "anomaly_type": "increase" if change > 0 else ("decrease" if change < 0 else "flat"),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


# Simple in-process metric windows registry
_WINDOWS: Dict[str, MetricWindow] = {}


def get_window(name: str, window_size: int = 20) -> MetricWindow:
    win = _WINDOWS.get(name)
    if win is None:
        win = MetricWindow(name=name, window_size=window_size)
        _WINDOWS[name] = win
    return win


