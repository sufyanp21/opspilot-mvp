import pandas as pd
import re
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from app.models.file import SourceFile
from app.models.span import SpanSnapshot, SpanDelta
from app.core.logging import logger

class SpanService:
    """Service for handling SPAN margin processing."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_span_file(self, source_file: SourceFile) -> Dict[str, Any]:
        """Process a SPAN margin file."""
        
        logger.info(f"Processing SPAN file: {source_file.original_name}")
        
        # Load CSV data
        df = pd.read_csv(source_file.stored_path)
        
        # Detect or extract date from filename
        asof_date = self._extract_date_from_filename(source_file.original_name)
        if not asof_date:
            # Try to find date in the data or use today
            asof_date = date.today()
        
        # Normalize column names (handle various SPAN formats)
        df = self._normalize_span_columns(df)
        
        # Validate required columns
        required_cols = ["product", "account", "scan_margin"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Store snapshots
        snapshots = self._store_snapshots(df, source_file.id, asof_date)
        
        # Calculate and store deltas
        deltas = await self._calculate_and_store_deltas(asof_date)
        
        logger.info(f"Processed {len(snapshots)} SPAN snapshots, calculated {len(deltas)} deltas")
        
        return {
            "asof_date": asof_date,
            "rows_ingested": len(snapshots),
            "deltas_calculated": len(deltas)
        }
    
    def _extract_date_from_filename(self, filename: str) -> Optional[date]:
        """Extract date from filename patterns like span_2025-08-08.csv."""
        
        # Pattern: YYYY-MM-DD
        pattern1 = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(pattern1, filename)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d").date()
            except ValueError:
                pass
        
        # Pattern: YYYYMMDD
        pattern2 = r'(\d{8})'
        match = re.search(pattern2, filename)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y%m%d").date()
            except ValueError:
                pass
        
        return None
    
    def _normalize_span_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize SPAN column names to standard format."""
        
        # Common column mappings
        column_mappings = {
            # Product variations
            "Product": "product",
            "PRODUCT": "product",
            "Instrument": "product",
            "Symbol": "product",
            "Contract": "product",
            
            # Account variations
            "Account": "account",
            "ACCOUNT": "account",
            "Account ID": "account",
            "AccountID": "account",
            "Acct": "account",
            
            # Margin variations
            "Scan Margin": "scan_margin",
            "SCAN_MARGIN": "scan_margin",
            "ScanMargin": "scan_margin",
            "Margin": "scan_margin",
            "SPAN Margin": "scan_margin",
            "Initial Margin": "scan_margin",
            "Requirement": "scan_margin"
        }
        
        # Apply mappings
        df = df.rename(columns=column_mappings)
        
        # Convert data types
        if "scan_margin" in df.columns:
            df["scan_margin"] = pd.to_numeric(df["scan_margin"], errors="coerce").fillna(0)
        
        # Fill missing values
        df = df.fillna("")
        
        return df
    
    def _store_snapshots(self, df: pd.DataFrame, file_id: uuid.UUID, asof_date: date) -> list:
        """Store SPAN snapshots in database."""
        
        snapshots = []
        for idx, row in df.iterrows():
            snapshot = SpanSnapshot(
                asof_date=asof_date,
                product=str(row["product"]),
                account=str(row["account"]),
                scan_margin=Decimal(str(row["scan_margin"])),
                file_id=file_id,
                row_number=idx + 1
            )
            snapshots.append(snapshot)
        
        self.db.bulk_save_objects(snapshots)
        self.db.commit()
        
        return snapshots
    
    async def _calculate_and_store_deltas(self, asof_date: date) -> list:
        """Calculate deltas between current and previous snapshots."""
        
        # Get current snapshots
        current_snapshots = self.db.query(SpanSnapshot).filter(
            SpanSnapshot.asof_date == asof_date
        ).all()
        
        # Find previous date with data
        previous_date = self.db.query(SpanSnapshot.asof_date).filter(
            SpanSnapshot.asof_date < asof_date
        ).order_by(SpanSnapshot.asof_date.desc()).first()
        
        if not previous_date:
            logger.info("No previous SPAN data found for delta calculation")
            return []
        
        previous_date = previous_date[0]
        
        # Get previous snapshots
        previous_snapshots = self.db.query(SpanSnapshot).filter(
            SpanSnapshot.asof_date == previous_date
        ).all()
        
        # Create lookup for previous snapshots
        previous_lookup = {
            (snap.product, snap.account): snap 
            for snap in previous_snapshots
        }
        
        # Calculate deltas
        deltas = []
        for current_snap in current_snapshots:
            key = (current_snap.product, current_snap.account)
            previous_snap = previous_lookup.get(key)
            
            scan_before = previous_snap.scan_margin if previous_snap else None
            scan_after = current_snap.scan_margin
            delta = scan_after - (scan_before or Decimal('0'))
            
            delta_record = SpanDelta(
                asof_date=asof_date,
                product=current_snap.product,
                account=current_snap.account,
                scan_before=scan_before,
                scan_after=scan_after,
                delta=delta,
                previous_snapshot_id=previous_snap.id if previous_snap else None,
                current_snapshot_id=current_snap.id
            )
            deltas.append(delta_record)
        
        self.db.bulk_save_objects(deltas)
        self.db.commit()
        
        logger.info(f"Calculated deltas between {previous_date} and {asof_date}")
        
        return deltas
