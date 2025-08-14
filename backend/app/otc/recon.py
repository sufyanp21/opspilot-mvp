from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .schemas import OTCTrade


def _uti_or_key(t: OTCTrade) -> str:
    if t.uti:
        return t.uti
    # Composite fallback: product|counterparty|notional|ccy|maturity
    maturity = t.maturity.isoformat() if t.maturity else ""
    return f"{t.product}|{t.counterparty}|{t.notional}|{t.ccy}|{maturity}"


def _index(trades: List[OTCTrade]) -> Dict[str, OTCTrade]:
    return {_uti_or_key(t): t for t in trades}


def _econ_diff(a: OTCTrade, b: OTCTrade) -> Dict[str, Tuple[object, object]]:
    diffs: Dict[str, Tuple[object, object]] = {}
    for field in [
        "product",
        "ccy",
        "notional",
        "fixed_rate",
        "float_idx",
        "maturity",
    ]:
        va = getattr(a, field)
        vb = getattr(b, field)
        if va != vb:
            diffs[field] = (va, vb)
    return diffs


def reconcile_otc(
    internal: List[OTCTrade],
    external: List[OTCTrade],
    tolerances: Optional[Dict[str, float]] = None,
):
    tolerances = tolerances or {"notional": 0.0, "fixed_rate": 0.0}
    i_map = _index(internal)
    e_map = _index(external)

    matches = 0
    mismatches: List[dict] = []
    missing_internal: List[str] = []
    missing_external: List[str] = []

    keys = set(i_map.keys()) | set(e_map.keys())
    for k in sorted(keys):
        i = i_map.get(k)
        e = e_map.get(k)
        if i and e:
            diffs = _econ_diff(i, e)
            if not diffs:
                matches += 1
            else:
                mismatches.append(
                    {
                        "key": k,
                        "diffs": {f: {"internal": v[0], "external": v[1]} for f, v in diffs.items()},
                    }
                )
        elif i and not e:
            missing_external.append(k)
        elif e and not i:
            missing_internal.append(k)

    exceptions: List[dict] = []
    for m in mismatches:
        within_notional = True
        within_rate = True
        if "notional" in m["diffs"]:
            n_int = float(m["diffs"]["notional"]["internal"] or 0)
            n_ext = float(m["diffs"]["notional"]["external"] or 0)
            within_notional = abs(n_ext - n_int) <= tolerances.get("notional", 0.0)
        if "fixed_rate" in m["diffs"]:
            r_int = float(m["diffs"]["fixed_rate"]["internal"] or 0)
            r_ext = float(m["diffs"]["fixed_rate"]["external"] or 0)
            within_rate = abs(r_ext - r_int) <= tolerances.get("fixed_rate", 0.0)
        exceptions.append(
            {
                "type": "FIELD_MISMATCH",
                "details": m["diffs"],
                "auto_cleared": within_notional and within_rate,
            }
        )
    for k in missing_external:
        exceptions.append({"type": "MISSING_EXTERNAL", "key": k})
    for k in missing_internal:
        exceptions.append({"type": "MISSING_INTERNAL", "key": k})

    return {
        "summary": {
            "matches": matches,
            "mismatches": len(mismatches),
            "missing_internal": len(missing_internal),
            "missing_external": len(missing_external),
        },
        "exceptions": exceptions,
    }


