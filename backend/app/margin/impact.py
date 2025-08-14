from __future__ import annotations

from typing import Any, Dict, List


def compute_margin_impact(unresolved_breaks: List[Dict[str, Any]], span_params: Dict[str, Any]) -> Dict[str, Any]:
    scanning = float(span_params.get("SPAN_SCANNING_RANGE", 15.0))
    credit = float(span_params.get("INTERCOMMODITY_CREDIT", 0.8))
    total_im_delta = 0.0
    items: List[Dict[str, Any]] = []
    for br in unresolved_breaks:
        qty = abs(float(br.get("details", {}).get("quantity", {}).get("external", 0) - br.get("details", {}).get("quantity", {}).get("internal", 0)))
        price_dev = abs(float(br.get("details", {}).get("price", {}).get("external", 0) - br.get("details", {}).get("price", {}).get("internal", 0)))
        im_delta = (qty * price_dev) * scanning / 100.0 * (1.0 - credit)
        items.append({"trade_id": br.get("trade_id"), "im_delta": im_delta})
        total_im_delta += im_delta
    return {"total_im_delta": total_im_delta, "items": items}


