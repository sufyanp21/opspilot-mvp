from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _auth_headers(email: str = "user@example.com"):
    res = client.post("/auth/login", json={"email": email, "password": "demo"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_public():
    assert client.get("/health").status_code == 200


def test_reconcile_requires_auth():
    assert client.post("/reconcile").status_code == 401


def test_reconcile_with_auth_but_missing_files():
    h = _auth_headers()
    res = client.post("/reconcile", headers=h)
    assert res.status_code == 400


