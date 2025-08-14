from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _auth_headers():
    res = client.post("/auth/login", json={"email": "user@example.com", "password": "demo"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_runs_list_without_db():
    h = _auth_headers()
    res = client.get("/runs/", headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["items"] == [] and body["total"] == 0


