from __future__ import annotations

from app.root_cause import classify_root_cause


def test_classify_missing_external():
    rc, conf, sug = classify_root_cause({"type": "MISSING_EXTERNAL"})
    assert rc.lower().startswith("external record missing")
    assert 0.5 < conf <= 1.0
    assert isinstance(sug, dict)


def test_classify_field_mismatch_quantity():
    rc, conf, sug = classify_root_cause({"type": "FIELD_MISMATCH", "cluster": "ESU5:ACC1"})
    assert "tolerance" in rc.lower() or "price" in rc.lower()
    assert 0.4 < conf <= 1.0

