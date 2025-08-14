from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _auth_headers():
    res = client.post("/auth/login", json={"email": "user@example.com", "password": "demo"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_export_exceptions_csv():
    h = _auth_headers()
    payload = {"exceptions": [{"type": "FIELD_MISMATCH", "severity": "HIGH", "trade_id": "T1", "cluster": None, "details": {"price": {"internal": 1, "external": 2}}}]}
    res = client.post("/runs/export/exceptions", headers=h, json=payload)
    assert res.status_code == 200
    assert res.headers.get("content-type", "").startswith("text/csv")
    assert b"trade_id" in res.content


