from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_success_and_refresh():
    res = client.post("/auth/login", json={"email": "user@example.com", "password": "demo"})
    assert res.status_code == 200, res.text
    tokens = res.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    res2 = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res2.status_code == 200, res2.text
    tokens2 = res2.json()
    assert tokens2["access_token"] != tokens["access_token"]


def test_login_failure():
    res = client.post("/auth/login", json={"email": "user@example.com", "password": "wrong"})
    assert res.status_code == 401


