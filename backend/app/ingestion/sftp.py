from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd

from .csv import parse_trade_csv, register_file


def fetch_and_parse_sftp(local_path: Path) -> List:
    """
    Dev stub for SFTP: in dev, read from local path; in prod, replace with Paramiko.
    """
    df = pd.read_csv(local_path)
    return parse_trade_csv(df)


def process_sftp_file(*, db, source: str, filename: str, content: bytes, force: bool = False) -> dict:
    """
    Register and parse a CSV delivered from SFTP. Returns registry info and parsed size.
    """
    reg = register_file(db, source=source, filename=filename, content=content, force=force)
    if reg.get("skipped"):
        return {"skipped": True}
    df = pd.read_csv(pd.io.common.BytesIO(content))  # type: ignore[attr-defined]
    trades = parse_trade_csv(df)
    return {"skipped": False, "parsed": len(trades)}


