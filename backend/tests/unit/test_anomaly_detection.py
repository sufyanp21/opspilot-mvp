from __future__ import annotations

from app.anomaly_detection import MetricWindow, detect_zscore, detect_pct_delta


def test_detect_zscore_flags_when_outlier():
    win = MetricWindow(name="match_rate", window_size=10)
    # Seed a stable window
    for v in [0.90, 0.91, 0.89, 0.90, 0.92, 0.91, 0.90, 0.89]:
        win.add(v)
    # Large drop should trigger anomaly
    alert = detect_zscore(win, current=0.75, z_threshold=2.0)
    assert alert["metric"] == "match_rate"
    assert alert["threshold"]["type"] == "zscore"
    assert alert["anomaly"] is True


def test_detect_pct_delta_triggers_on_threshold():
    alert = detect_pct_delta("SPAN_SCANNING_RANGE", old=10.0, new=12.0, pct_threshold=0.1)
    assert alert["metric"] == "SPAN_SCANNING_RANGE"
    assert alert["threshold"]["type"] == "pct"
    assert alert["anomaly"] is True

