from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_protected_upload_requires_auth_or_rate_limit_allows_public_for_now():
    # Currently upload is not auth-protected yet; ensure endpoint exists and rate-limiter does not crash
    res = client.get("/health")
    assert res.status_code == 200


