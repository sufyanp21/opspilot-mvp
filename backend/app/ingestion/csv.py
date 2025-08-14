from __future__ import annotations

from typing import List, Optional

import pandas as pd
from pydantic import ValidationError

from ..schemas_cdm import Trade
from ..models import FileRegistry
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import hashlib


REQUIRED_COLUMNS = {"trade_id", "product_code", "quantity", "price"}


REQUIRED_COLS = {"trade_id", "product_code", "quantity", "price"}


def parse_trade_csv(df: pd.DataFrame) -> List[Trade]:
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    # Normalize all column names to lowercase
    df = df.rename(columns={c: c.lower() for c in df.columns})
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(list(missing))}")

    # Normalize types and build Trades
    trades: List[Trade] = []
    for _, row in df.iterrows():
        data = {
            "trade_id": str(row.get("trade_id")),
            "product_code": str(row.get("product_code")),
            "account": row.get("account"),
            "quantity": float(row.get("quantity")),
            "price": float(row.get("price")),
            "party_internal": row.get("party_internal"),
            "party_external": row.get("party_external"),
        }
        try:
            trades.append(Trade(**data))
        except ValidationError as ve:
            raise ValueError(f"Invalid row for trade_id={data.get('trade_id')}: {ve}")
    return trades


_seen_hashes_memory: set[str] = set()


def register_file(db: Session | None, *, source: str, filename: str, content: bytes, force: bool = False) -> dict:
    sha = hashlib.sha256(content).hexdigest()
    if db is None:
        if not force:
            if sha in _seen_hashes_memory:
                return {"sha256": sha, "skipped": True}
            _seen_hashes_memory.add(sha)
        return {"sha256": sha, "skipped": False}
    existing = db.query(FileRegistry).filter_by(sha256=sha).first()
    if existing and not force:
        return {"sha256": sha, "skipped": True}
    row = FileRegistry(
        source=source,
        filename=filename,
        size=len(content),
        sha256=sha,
        received_at=datetime.now(timezone.utc),
        status="received",
    )
    db.add(row)
    db.commit()
    return {"sha256": sha, "skipped": False}


