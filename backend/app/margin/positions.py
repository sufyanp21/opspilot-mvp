from __future__ import annotations

from typing import Any, Dict, List


def compute_im_vm_from_positions(positions: List[Dict[str, Any]], span_params: Dict[str, Any]) -> Dict[str, Any]:
    scanning = float(span_params.get("SPAN_SCANNING_RANGE", 15.0))
    credit = float(span_params.get("INTERCOMMODITY_CREDIT", 0.8))
    im_total = 0.0
    vm_total = 0.0
    items: List[Dict[str, Any]] = []
    for p in positions:
        qty = abs(float(p.get("net_quantity", 0)))
        price = float(p.get("price", 0) or 0)
        prev_price = float(p.get("prev_price", price) or 0)
        im = qty * price * scanning / 100.0 * (1.0 - credit)
        vm = qty * (price - prev_price)
        items.append({"product_code": p.get("product_code"), "im": im, "vm": vm})
        im_total += im
        vm_total += vm
    return {"im_total": im_total, "vm_total": vm_total, "items": items}


