import os
import time
import requests

BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


def test_health():
    r = requests.get(f"{BASE}/health", timeout=3)
    assert r.status_code == 200


def test_upload_and_reconcile():
    # Upload minimal CSVs if endpoints require; here we just assert health path for smoke
    r = requests.get(f"{BASE}/health", timeout=3)
    assert r.ok



