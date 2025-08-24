from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _auth_headers(email: str = "demo+admin@opspilot.ai", password: str = "demo") -> dict[str, str]:
    client = TestClient(app)
    r = client.post("/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_train_and_score_predict_breaks():
    client = TestClient(app)
    headers = _auth_headers()

    r_train = client.post("/ml/train/predict-breaks", headers=headers)
    assert r_train.status_code == 200
    model_id = r_train.json()["model_id"]
    assert model_id.startswith("predict_breaks_v1_")

    r_score = client.post("/ml/score/predict-breaks", headers=headers, params={"runId": "TEST_RUN_1"})
    assert r_score.status_code == 200
    body = r_score.json()
    assert "counts" in body and "total" in body and body["total"] > 0

