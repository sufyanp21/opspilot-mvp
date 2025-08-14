from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _analyst_headers():
    res = client.post("/auth/login", json={"email": "user@example.com", "password": "demo"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_only_suppress_denied_for_analyst():
    h = _analyst_headers()
    resp = client.post("/breaks/1/suppress", headers=h)
    assert resp.status_code == 403


