from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_recon_config(path: str | Path | None = None) -> Dict[str, Any]:
    default = {
        "tolerances": {
            "price": {"abs": 0.0, "pct": 0.0},
            "quantity": {"abs": 0.0, "pct": 0.0},
            "amount": {"abs": 0.0, "pct": 0.0},
            "datetime_minutes": 0,
        },
        "product_overrides": {},
        "prefer_identifiers": ["uti", "upi", "trade_id"],
    }
    if path is None:
        return default
    p = Path(path)
    if not p.exists():
        return default
    data = yaml.safe_load(p.read_text()) or {}
    # shallow merge for top-level keys
    out = {**default, **data}
    out["tolerances"] = {**default["tolerances"], **(data.get("tolerances") or {})}
    out["product_overrides"] = {**default["product_overrides"], **(data.get("product_overrides") or {})}
    return out


