import pandas as pd
import json
import uuid
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.file import SourceFile
from app.models.trade import TradeInternal, TradeCleared
from app.models.recon import ReconException, ExceptionStatus
from app.core.logging import logger

class ReconciliationService:
    """Service for handling trade reconciliation logic."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def run_reconciliation(
        self,
        run_id: uuid.UUID,
        internal_file: SourceFile,
        cleared_file: SourceFile,
        column_map: Dict[str, Dict[str, str]],
        match_keys: List[str],
        tolerances: Dict[str, int]
    ) -> Dict[str, Any]:
        """Run reconciliation between internal and cleared trades."""
        
        logger.info(f"Starting reconciliation run {run_id}")
        
        # Load and normalize data
        internal_df = self._load_and_normalize_csv(
            internal_file.stored_path, 
            column_map["internal"]
        )
        cleared_df = self._load_and_normalize_csv(
            cleared_file.stored_path, 
            column_map["cleared"]
        )
        
        # Store normalized data in database
        self._store_trades(internal_df, internal_file.id, TradeInternal)
        self._store_trades(cleared_df, cleared_file.id, TradeCleared)
        
        # Perform reconciliation
        matches, exceptions = self._reconcile_trades(
            internal_df, cleared_df, match_keys, tolerances
        )
        
        # Store exceptions
        self._store_exceptions(run_id, exceptions)
        
        # Calculate summary
        total_internal = len(internal_df)
        total_cleared = len(cleared_df)
        total = max(total_internal, total_cleared)
        matched = len(matches)
        mismatched = len(exceptions)
        pct_matched = (matched / total * 100) if total > 0 else 0
        
        summary = {
            "total": total,
            "matched": matched,
            "mismatched": mismatched,
            "pct_matched": round(pct_matched, 2)
        }
        
        logger.info(f"Reconciliation completed: {summary}")
        
        return {
            "summary": summary,
            "exceptions": [self._format_exception(exc) for exc in exceptions]
        }
    
    def _load_and_normalize_csv(self, file_path: str, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """Load CSV and normalize column names."""
        
        df = pd.read_csv(file_path)
        
        # Apply column mapping
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_cols = ["trade_id", "account", "symbol", "side", "qty", "price", "trade_date"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        # Convert data types
        df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
        df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce").dt.date
        
        # Fill missing values
        df = df.fillna("")
        
        return df
    
    def _store_trades(self, df: pd.DataFrame, file_id: uuid.UUID, model_class):
        """Store normalized trades in database."""
        
        trades = []
        for idx, row in df.iterrows():
            trade = model_class(
                trade_id=str(row["trade_id"]),
                account=str(row["account"]),
                symbol=str(row["symbol"]),
                side=row["side"] if row["side"] in ["BUY", "SELL"] else "BUY",
                qty=int(row["qty"]),
                price=Decimal(str(row["price"])),
                trade_date=row["trade_date"],
                exchange=str(row.get("exchange", "")),
                clearing_ref=str(row.get("clearing_ref", "")),
                source_file_id=file_id,
                row_number=idx + 1,
                raw_data=json.dumps(row.to_dict(), default=str)
            )
            trades.append(trade)
        
        self.db.bulk_save_objects(trades)
        self.db.commit()
        
        logger.info(f"Stored {len(trades)} {model_class.__name__} records")
    
    def _reconcile_trades(
        self, 
        internal_df: pd.DataFrame, 
        cleared_df: pd.DataFrame, 
        match_keys: List[str],
        tolerances: Dict[str, int]
    ) -> tuple[List[Dict], List[Dict]]:
        """Perform trade reconciliation."""
        
        matches = []
        exceptions = []
        
        # Create composite keys
        internal_df["_match_key"] = internal_df[match_keys].astype(str).agg("||".join, axis=1)
        cleared_df["_match_key"] = cleared_df[match_keys].astype(str).agg("||".join, axis=1)
        
        # Find matches and exceptions
        internal_keys = set(internal_df["_match_key"])
        cleared_keys = set(cleared_df["_match_key"])
        
        # Process matched keys
        matched_keys = internal_keys.intersection(cleared_keys)
        for key in matched_keys:
            internal_rows = internal_df[internal_df["_match_key"] == key]
            cleared_rows = cleared_df[cleared_df["_match_key"] == key]
            
            # For simplicity, take first row if multiple matches
            internal_row = internal_rows.iloc[0]
            cleared_row = cleared_rows.iloc[0]
            
            # Check tolerances
            is_match, diffs = self._check_tolerances(internal_row, cleared_row, tolerances)
            
            if is_match:
                matches.append({
                    "key": key,
                    "internal": internal_row.to_dict(),
                    "cleared": cleared_row.to_dict()
                })
            else:
                exceptions.append({
                    "keys": self._extract_keys(internal_row, match_keys),
                    "internal": internal_row.to_dict(),
                    "cleared": cleared_row.to_dict(),
                    "diff": diffs,
                    "status": "OPEN"
                })
        
        # Process unmatched internal trades
        unmatched_internal = internal_keys - cleared_keys
        for key in unmatched_internal:
            internal_row = internal_df[internal_df["_match_key"] == key].iloc[0]
            exceptions.append({
                "keys": self._extract_keys(internal_row, match_keys),
                "internal": internal_row.to_dict(),
                "cleared": None,
                "diff": {"status": "missing_in_cleared"},
                "status": "OPEN"
            })
        
        # Process unmatched cleared trades
        unmatched_cleared = cleared_keys - internal_keys
        for key in unmatched_cleared:
            cleared_row = cleared_df[cleared_df["_match_key"] == key].iloc[0]
            exceptions.append({
                "keys": self._extract_keys(cleared_row, match_keys),
                "internal": None,
                "cleared": cleared_row.to_dict(),
                "diff": {"status": "missing_in_internal"},
                "status": "OPEN"
            })
        
        return matches, exceptions
    
    def _check_tolerances(self, internal_row: pd.Series, cleared_row: pd.Series, tolerances: Dict[str, int]) -> tuple[bool, Dict]:
        """Check if trades match within tolerances."""
        
        diffs = {}
        is_match = True
        
        # Check quantity tolerance
        qty_diff = abs(int(internal_row["qty"]) - int(cleared_row["qty"]))
        if qty_diff > tolerances.get("qty", 0):
            is_match = False
            diffs["qty"] = qty_diff
        
        # Check price tolerance (in ticks)
        price_internal = float(internal_row["price"])
        price_cleared = float(cleared_row["price"])
        tick_size = 0.25  # Default tick size
        price_ticks = round(abs(price_internal - price_cleared) / tick_size)
        
        if price_ticks > tolerances.get("price_ticks", 1):
            is_match = False
            diffs["price_ticks"] = price_ticks
        
        return is_match, diffs
    
    def _extract_keys(self, row: pd.Series, match_keys: List[str]) -> Dict[str, Any]:
        """Extract matching keys from a row."""
        return {key: str(row[key]) for key in match_keys}
    
    def _store_exceptions(self, run_id: uuid.UUID, exceptions: List[Dict]):
        """Store exceptions in database."""
        
        exception_records = []
        for exc in exceptions:
            exception_record = ReconException(
                run_id=run_id,
                keys_json=json.dumps(exc["keys"]),
                internal_json=json.dumps(exc["internal"], default=str) if exc["internal"] else None,
                cleared_json=json.dumps(exc["cleared"], default=str) if exc["cleared"] else None,
                diff_json=json.dumps(exc["diff"], default=str),
                status=ExceptionStatus.OPEN
            )
            exception_records.append(exception_record)
        
        self.db.bulk_save_objects(exception_records)
        self.db.commit()
        
        logger.info(f"Stored {len(exception_records)} exceptions")
    
    def _format_exception(self, exc: Dict) -> Dict:
        """Format exception for API response."""
        return {
            "id": str(uuid.uuid4()),  # Temporary ID for response
            "keys": exc["keys"],
            "internal": exc["internal"],
            "cleared": exc["cleared"],
            "diff": exc["diff"],
            "status": exc["status"]
        }
