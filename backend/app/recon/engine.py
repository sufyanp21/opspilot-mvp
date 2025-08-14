from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from ..schemas_cdm import Trade
from ..config_loader import load_recon_config


def _preferred_key(t: Trade, prefer: List[str]) -> str:
    for k in prefer:
        if k == "uti" and getattr(t, "uti", None):
            return t.uti  # type: ignore[return-value]
        if k == "upi" and getattr(t, "upi", None):
            return t.upi  # type: ignore[return-value]
        if k == "trade_id" and t.trade_id:
            return t.trade_id
    return t.trade_id


def _index_by_preferred(trades: List[Trade], prefer: List[str]) -> Dict[str, Trade]:
    return {_preferred_key(t, prefer): t for t in trades}

def _composite_key(t: Trade) -> str:
    # trade date missing in schema; use product_code+account+price as pragmatic composite
    return f"{t.product_code}|{t.account}|{t.price}|{t.quantity}"

def _index_by_composite(trades: List[Trade]) -> Dict[str, Trade]:
    return {_composite_key(t): t for t in trades}

def _trade_diff(a: Trade, b: Trade) -> Dict[str, Tuple[object, object]]:
    diffs: Dict[str, Tuple[object, object]] = {}
    for field in ["product_code", "account", "quantity", "price"]:
        va = getattr(a, field)
        vb = getattr(b, field)
        if va != vb:
            diffs[field] = (va, vb)
    return diffs


def _severity_from_diffs(diffs: Dict[str, Tuple[object, object]]) -> str:
    if not diffs:
        return "NONE"
    if "price" in diffs or "quantity" in diffs:
        return "HIGH"
    return "MEDIUM"


def _root_cause_explanation(diffs: Dict[str, Tuple[object, object]]) -> str:
    if "quantity" in diffs and "price" in diffs:
        return "Both quantity and price differ; likely allocation or stale price."
    if "quantity" in diffs:
        return "Quantity mismatch; check fills, average price aggregation, or booking."
    if "price" in diffs:
        return "Price deviation; review tick size, rounding, or stale market data."
    if "account" in diffs:
        return "Account mismatch; verify account mapping or broker statement."
    if "product_code" in diffs:
        return "Product mapping discrepancy; verify symbol/series and expiry."
    return "General discrepancy."


def reconcile_trades(internal: List[Trade], external: List[Trade], tolerances: Optional[Dict[str, float]] = None, recon_config_path: Optional[str] = None):
    config = load_recon_config(recon_config_path)
    prefer_ids: List[str] = config.get("prefer_identifiers", ["trade_id"])
    tol_cfg = config.get("tolerances", {})
    # legacy tolerances parameter support
    if tolerances is not None:
        tol_cfg = {"price": {"abs": tolerances.get("price", 0.0)}, "quantity": {"abs": tolerances.get("quantity", 0.0)}}

    i_map = _index_by_preferred(internal, prefer_ids)
    e_map = _index_by_preferred(external, prefer_ids)
    # Build composite indices for fallback
    i_comp = _index_by_composite(internal)
    e_comp = _index_by_composite(external)

    matches = 0
    mismatches: List[dict] = []
    missing_internal: List[str] = []
    missing_external: List[str] = []

    all_ids = set(i_map.keys()) | set(e_map.keys())
    for tid in sorted(all_ids):
        i = i_map.get(tid)
        e = e_map.get(tid)
        if i and e:
            diffs = _trade_diff(i, e)
            if not diffs:
                matches += 1
            else:
                mismatches.append(
                    {
                        "trade_id": tid,
                        "diffs": {k: {"internal": v[0], "external": v[1]} for k, v in diffs.items()},
                        "severity": _severity_from_diffs(diffs),
                        "cluster_key": f"{i.product_code}:{i.account}",
                        "root_cause": _root_cause_explanation(diffs),
                    }
                )
        elif i and not e:
            missing_external.append(tid)
        elif e and not i:
            # Try composite fallback
            comp = _composite_key(e)
            internal_fb = i_comp.get(comp)
            if internal_fb:
                diffs = _trade_diff(internal_fb, e)
                mismatches.append(
                    {
                        "trade_id": internal_fb.trade_id,
                        "diffs": {k: {"internal": v[0], "external": v[1]} for k, v in diffs.items()},
                        "severity": _severity_from_diffs(diffs),
                        "cluster_key": f"{internal_fb.product_code}:{internal_fb.account}",
                        "root_cause": _root_cause_explanation(diffs),
                    }
                )
            else:
                missing_internal.append(tid)

    summary = {
        "total_internal": len(internal),
        "total_external": len(external),
        "matches": matches,
        "mismatches": len(mismatches),
        "missing_internal": len(missing_internal),
        "missing_external": len(missing_external),
    }

    exceptions: List[dict] = []
    for m in mismatches:
        # Auto-clear low-impact within tolerance
        # absolute thresholds
        price_abs = tol_cfg.get("price", {}).get("abs", 0.0)
        qty_abs = tol_cfg.get("quantity", {}).get("abs", 0.0)
        # percent thresholds relative to external value
        price_pct = tol_cfg.get("price", {}).get("pct", 0.0)
        qty_pct = tol_cfg.get("quantity", {}).get("pct", 0.0)
        if "price" in m["diffs"]:
            p_int = m["diffs"]["price"]["internal"]
            p_ext = m["diffs"]["price"]["external"]
            p_diff = abs((p_ext or 0) - (p_int or 0))
            p_tol = max(price_abs, abs(p_ext or 0) * price_pct)
            within_price = p_diff <= p_tol
        else:
            within_price = True
        if "quantity" in m["diffs"]:
            q_int = m["diffs"]["quantity"]["internal"]
            q_ext = m["diffs"]["quantity"]["external"]
            q_diff = abs((q_ext or 0) - (q_int or 0))
            q_tol = max(qty_abs, abs(q_ext or 0) * qty_pct)
            within_qty = q_diff <= q_tol
        else:
            within_qty = True
        auto_cleared = within_price and within_qty
        exceptions.append(
            {
                "type": "FIELD_MISMATCH",
                "severity": m["severity"],
                "trade_id": m["trade_id"],
                "cluster": m["cluster_key"],
                "details": m["diffs"],
                "root_cause": m.get("root_cause"),
                "auto_cleared": auto_cleared,
            }
        )
    for tid in missing_external:
        exceptions.append(
            {"type": "MISSING_EXTERNAL", "severity": "HIGH", "trade_id": tid, "cluster": None, "details": {}}
        )
    for tid in missing_internal:
        exceptions.append(
            {"type": "MISSING_INTERNAL", "severity": "HIGH", "trade_id": tid, "cluster": None, "details": {}}
        )

    return {"summary": summary, "exceptions": exceptions}


