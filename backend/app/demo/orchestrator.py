from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from ..ingestion import csv as csv_ing
from ..recon.engine import reconcile_trades
from ..risk.span import diff_span_params


def run_demo(base_dir: Path) -> Dict[str, Any]:
    # Load internal and CME positions as proxies for recon
    sample_dir = base_dir / "sample_data"
    
    # Check if sample data exists
    internal_path = sample_dir / "internal_trades.csv"
    cme_path = sample_dir / "cme_positions_20250812.csv"
    
    if not internal_path.exists():
        return {"error": f"Sample data not found at {internal_path}. Please ensure sample_data/ directory exists with required files."}
    if not cme_path.exists():
        return {"error": f"Sample data not found at {cme_path}. Please ensure sample_data/ directory exists with required files."}
    
    try:
        internal = pd.read_csv(internal_path)
        cme = pd.read_csv(cme_path)
    except Exception as e:
        return {"error": f"Failed to load sample data: {str(e)}"}

    # Map CME positions to trade-like rows for demo
    cme_df = pd.DataFrame(
        {
            "trade_id": [f"EX_{i}" for i in range(len(cme))],
            "product_code": cme["Product Code"],
            "account": cme["Account"],
            "quantity": cme["Quantity"].astype(float),
            "price": cme["Price"].astype(float),
        }
    )

    internal_df = pd.DataFrame(
        {
            "trade_id": internal["Trade ID"],
            "product_code": internal["Product"],
            "account": internal["Account"],
            "quantity": internal["Quantity"].astype(float),
            "price": internal["Price"].astype(float),
        }
    )

    try:
        internal_trades = csv_ing.parse_trade_csv(internal_df)
        external_trades = csv_ing.parse_trade_csv(cme_df)
        recon = reconcile_trades(internal_trades, external_trades)
    except Exception as e:
        return {"error": f"Reconciliation failed: {str(e)}"}

    # Risk changes (SPAN): read current and simulate yesterday
    span_today = {
        "SPAN_SCANNING_RANGE": 12.5,
        "INTERCOMMODITY_CREDIT": 0.8,
        "DELTA_SCALER": 1.0,
    }
    span_yday = {
        "SPAN_SCANNING_RANGE": 11.0,
        "INTERCOMMODITY_CREDIT": 0.75,
        "DELTA_SCALER": 1.0,
    }
    span_diff = diff_span_params(span_today, span_yday)

    kpis = {
        "matches": recon["summary"]["matches"],
        "mismatches": recon["summary"]["mismatches"],
        "missing_internal": recon["summary"]["missing_internal"],
        "missing_external": recon["summary"]["missing_external"],
        "span_changes": len(span_diff),
    }

    return {
        "kpis": kpis,
        "exceptions": recon.get("exceptions", []),
        "span": span_diff,
    }


