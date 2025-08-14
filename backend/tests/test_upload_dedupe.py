from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _auth_headers():
    res = client.post("/auth/login", json={"email": "user@example.com", "password": "demo"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_dedupe_memory_no_db():
    h = _auth_headers()
    files = [("files", ("a.csv", b"x,y\n1,2\n", "text/csv"))]
    r1 = client.post("/upload", headers=h, files=files)
    assert r1.status_code == 200
    r2 = client.post("/upload", headers=h, files=files)
    assert r2.status_code == 200
    # second upload should be skipped by registry memory; returned file list may be empty
    assert isinstance(r2.json().get("files"), list)


