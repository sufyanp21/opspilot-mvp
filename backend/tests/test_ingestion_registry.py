from __future__ import annotations

from app.ingestion.csv import register_file


def test_register_file_no_db():
    out = register_file(None, source="upload", filename="a.csv", content=b"x,y\n1,2\n")
    assert out["sha256"] and out["skipped"] is False


