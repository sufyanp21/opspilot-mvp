from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from ..ingestion import csv as csv_ing
from ..recon.engine import reconcile_trades
from ..risk.span import diff_span_params


def _find_sample_dir(base_dir: Path) -> Path | None:
    """Return the first existing sample_data directory among common locations."""
    candidates = [
        base_dir / "sample_data",  # when base_dir is repo root
        (base_dir / ".." / "sample_data").resolve(),  # when base_dir is backend/
        Path(__file__).resolve().parents[3] / "sample_data",  # repo root from this file
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    return None


def _pick_col(df: pd.DataFrame, names: list[str], fallback_idx: int) -> pd.Series:
    for n in names:
        if n in df.columns:
            return df[n]
    return df.iloc[:, fallback_idx]


def run_demo(base_dir: Path) -> Dict[str, Any]:
    # Resolve sample data directory robustly
    sample_dir = _find_sample_dir(base_dir)
    if sample_dir is None:
        return {"error": f"Sample data directory not found. Tried under: {[str(base_dir / 'sample_data'), str((base_dir / '..' / 'sample_data').resolve())]}"}

    # Expected files
    internal_path = sample_dir / "internal_trades.csv"
    cme_path = sample_dir / "cme_positions_20250812.csv"

    internal: pd.DataFrame | None = None
    cme: pd.DataFrame | None = None
    try:
        if cme_path.exists():
            cme = pd.read_csv(cme_path)
        else:
            # Synthesize a small CME dataset if missing
            cme = pd.DataFrame(
                {
                    "Product Code": ["ESU5", "NQU5", "CLZ5", "GCZ5"],
                    "Account": ["ACC1", "ACC1", "ACC2", "ACC3"],
                    "Quantity": [10, -5, 7, 3],
                    "Price": [4925.5, 18985.25, 72.1, 2381.3],
                }
            )
    except Exception as e:
        return {"error": f"Failed to load CME sample data: {str(e)}"}

    # If internal is missing, synthesize from CME with small perturbations
    if internal_path.exists():
        try:
            internal = pd.read_csv(internal_path)
        except Exception as e:
            return {"error": f"Failed to load internal sample data: {str(e)}"}
    elif cme is not None and not cme.empty:
        # Create a synthetic internal set by tweaking CME rows
        try:
            prod = _pick_col(cme, ["Product Code", "product", "symbol"], 0)
            acct = _pick_col(cme, ["Account", "account"], 1)
            qty = pd.to_numeric(_pick_col(cme, ["Quantity", "qty"], 2), errors="coerce").fillna(0.0)
            price = pd.to_numeric(_pick_col(cme, ["Price", "price"], 3), errors="coerce").fillna(0.0)
            internal = pd.DataFrame(
                {
                    "Trade ID": [f"INT_{i}" for i in range(len(cme))],
                    "Product": prod,
                    "Account": acct,
                    # small perturbation to create mismatches and matches
                    "Quantity": (qty * 1.0).round(0),
                    "Price": (price * 1.0).round(2),
                }
            )
        except Exception as e:
            return {"error": f"Failed to synthesize internal trades: {str(e)}"}
    else:
        # Generate both sides entirely if nothing exists
        prod = _pick_col(cme, ["Product Code", "product", "symbol"], 0)
        acct = _pick_col(cme, ["Account", "account"], 1)
        qty = pd.to_numeric(_pick_col(cme, ["Quantity", "qty"], 2), errors="coerce").fillna(0.0)
        price = pd.to_numeric(_pick_col(cme, ["Price", "price"], 3), errors="coerce").fillna(0.0)
        internal = pd.DataFrame(
            {
                "Trade ID": [f"INT_{i}" for i in range(len(cme))],
                "Product": prod,
                "Account": acct,
                "Quantity": (qty * 1.0).round(0),
                "Price": (price * 1.0).round(2),
            }
        )

    # Map CME positions to trade-like rows for demo
    prod_c = _pick_col(cme, ["Product Code", "product", "symbol"], 0)
    acct_c = _pick_col(cme, ["Account", "account"], 1)
    qty_c = pd.to_numeric(_pick_col(cme, ["Quantity", "qty"], 2), errors="coerce").fillna(0.0)
    price_c = pd.to_numeric(_pick_col(cme, ["Price", "price"], 3), errors="coerce").fillna(0.0)
    cme_df = pd.DataFrame(
        {
            "trade_id": [f"EX_{i}" for i in range(len(cme))],
            "product_code": prod_c,
            "account": acct_c,
            "quantity": qty_c,
            "price": price_c,
        }
    )

    trade_i = _pick_col(internal, ["Trade ID", "trade_id"], 0)
    prod_i = _pick_col(internal, ["Product", "product", "symbol"], 1)
    acct_i = _pick_col(internal, ["Account", "account"], 2)
    qty_i = pd.to_numeric(_pick_col(internal, ["Quantity", "qty"], 3), errors="coerce").fillna(0.0)
    price_i = pd.to_numeric(_pick_col(internal, ["Price", "price"], 4), errors="coerce").fillna(0.0)
    internal_df = pd.DataFrame(
        {
            "trade_id": trade_i,
            "product_code": prod_i,
            "account": acct_i,
            "quantity": qty_i,
            "price": price_i,
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


