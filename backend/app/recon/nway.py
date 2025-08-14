from __future__ import annotations

from typing import Dict, List, Optional

from ..schemas_cdm import Trade


def reconcile_nway(
    internal: List[Trade], broker: List[Trade], ccp: List[Trade],
    authoritative_order: List[str] = ["ccp", "broker", "internal"],
    tolerances: Optional[Dict[str, float]] = None,
):
    tolerances = tolerances or {"price": 0.0, "quantity": 0.0}
    # Build indices
    i_map = {t.trade_id: t for t in internal}
    b_map = {t.trade_id: t for t in broker}
    c_map = {t.trade_id: t for t in ccp}
    all_ids = set(i_map) | set(b_map) | set(c_map)

    exceptions: List[Dict] = []
    matches = 0
    for tid in sorted(all_ids):
        records = {
            "internal": i_map.get(tid),
            "broker": b_map.get(tid),
            "ccp": c_map.get(tid),
        }
        present = [k for k, v in records.items() if v is not None]
        if len(present) == 3:
            # Check agreement using authoritative priority
            auth = next(src for src in authoritative_order if records[src] is not None)
            auth_rec = records[auth]
            disagreements: Dict[str, Dict] = {}
            for src, rec in records.items():
                if src == auth or rec is None or auth_rec is None:
                    continue
                price_ok = abs((rec.price or 0) - (auth_rec.price or 0)) <= tolerances.get("price", 0.0)
                qty_ok = abs((rec.quantity or 0) - (auth_rec.quantity or 0)) <= tolerances.get("quantity", 0.0)
                if not (price_ok and qty_ok):
                    disagreements[src] = {
                        "price": {"auth": auth_rec.price, src: rec.price},
                        "quantity": {"auth": auth_rec.quantity, src: rec.quantity},
                    }
            if not disagreements:
                matches += 1
            else:
                exceptions.append(
                    {
                        "type": "NWAY_DISAGREEMENT",
                        "trade_id": tid,
                        "authoritative": auth,
                        "details": disagreements,
                    }
                )
        else:
            missing = [s for s in ["internal", "broker", "ccp"] if s not in present]
            exceptions.append(
                {"type": "NWAY_MISSING", "trade_id": tid, "missing": missing, "authoritative": None}
            )

    return {"matches": matches, "exceptions": exceptions}


