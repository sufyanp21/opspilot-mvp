"""Enhanced reconciliation service with ETD engine and product-aware tolerances."""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.reconciliation.engines.etd_recon_engine import ETDReconEngine, ReconConfig
from app.reconciliation.tolerance.numeric_tolerance import ToleranceConfig
from app.core.enums import PriceToleranceMode
from app.config.config_loader import ConfigLoader
from app.models.trade import TradeInternal, TradeCleared
from app.models.recon import ReconRun, ReconException, ReconStatus
from app.models.product import Product
from app.services.recon_service import ReconciliationService

logger = logging.getLogger(__name__)


class EnhancedReconciliationService(ReconciliationService):
    """Enhanced reconciliation service with product-aware tick tolerances."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.config_loader = ConfigLoader()
    
    def run_etd_reconciliation(
        self,
        internal_file_id: str,
        cleared_file_id: str,
        column_mapping: Dict[str, Dict[str, str]],
        match_keys: List[str] = None,
        tolerances: Dict[str, Any] = None,
        product_overrides: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Run ETD reconciliation with product-aware tick tolerances.
        
        Args:
            internal_file_id: ID of internal trades file
            cleared_file_id: ID of cleared trades file
            column_mapping: Column mapping configuration
            match_keys: Fields to use for matching trades
            tolerances: Tolerance configuration
            product_overrides: Product-specific tolerance overrides
            
        Returns:
            Reconciliation results with enhanced metrics
        """
        logger.info(f"Starting ETD reconciliation: internal={internal_file_id}, cleared={cleared_file_id}")
        
        # Set defaults
        if match_keys is None:
            match_keys = ["trade_date", "account", "symbol"]
        
        if tolerances is None:
            tolerances = {
                "price": {"mode": "TICKS", "max_ticks": 1},
                "qty": {"mode": "ABSOLUTE", "max": 0}
            }
        
        # Create reconciliation run record
        recon_run = ReconRun(
            status=ReconStatus.RUNNING,
            internal_file_id=internal_file_id,
            cleared_file_id=cleared_file_id,
            column_mapping=column_mapping,
            tolerances=tolerances
        )
        self.db.add(recon_run)
        self.db.commit()
        
        try:
            # Load and normalize trade data
            internal_trades = self._load_internal_trades(internal_file_id)
            cleared_trades = self._load_cleared_trades(cleared_file_id)
            
            logger.info(f"Loaded {len(internal_trades)} internal and {len(cleared_trades)} cleared trades")
            
            # Create reconciliation configuration
            recon_config = self._create_etd_config(
                match_keys=match_keys,
                tolerances=tolerances,
                product_overrides=product_overrides or {}
            )
            
            # Run ETD reconciliation
            engine = ETDReconEngine(self.db, recon_config)
            matches, metrics = engine.reconcile(internal_trades, cleared_trades)
            
            # Create exception records
            exceptions = engine.create_exceptions(matches, str(recon_run.id))
            for exception in exceptions:
                self.db.add(exception)
            
            # Update run with results
            recon_run.status = ReconStatus.COMPLETED
            recon_run.summary = {
                **metrics,
                "run_completed_at": datetime.utcnow().isoformat(),
                "total_exceptions": len(exceptions),
                "etd_enhanced": True
            }
            
            self.db.commit()
            
            logger.info(f"ETD reconciliation completed: {metrics}")
            
            return {
                "run_id": str(recon_run.id),
                "status": "completed",
                "summary": recon_run.summary,
                "exceptions_count": len(exceptions),
                "enhanced_metrics": {
                    "tick_breaks": metrics.get("breaks_over_ticks_total", 0),
                    "perfect_matches": metrics.get("perfect_matches", 0),
                    "tolerance_matches": metrics.get("tolerance_matches", 0),
                    "match_rate_pct": metrics.get("match_rate_pct", 0.0)
                }
            }
            
        except Exception as e:
            logger.error(f"ETD reconciliation failed: {e}")
            recon_run.status = ReconStatus.FAILED
            recon_run.error_message = str(e)
            self.db.commit()
            
            return {
                "run_id": str(recon_run.id),
                "status": "failed",
                "error": str(e)
            }
    
    def _create_etd_config(
        self,
        match_keys: List[str],
        tolerances: Dict[str, Any],
        product_overrides: Dict[str, str]
    ) -> ReconConfig:
        """Create ETD reconciliation configuration."""
        
        # Parse price tolerance
        price_tolerance_dict = tolerances.get("price", {"mode": "TICKS", "max_ticks": 1})
        price_tolerance = self.config_loader._parse_tolerance_config(price_tolerance_dict)
        
        # Parse quantity tolerance
        qty_tolerance_dict = tolerances.get("qty", {"mode": "ABSOLUTE", "max": 0})
        qty_tolerance = self.config_loader._parse_tolerance_config(qty_tolerance_dict)
        
        # Create configuration with product overrides
        return self.config_loader.create_recon_config(
            match_keys=match_keys,
            default_price_tolerance=price_tolerance_dict,
            default_qty_tolerance=qty_tolerance_dict,
            product_overrides=product_overrides
        )
    
    def _load_internal_trades(self, file_id: str) -> List[TradeInternal]:
        """Load internal trades for reconciliation."""
        return self.db.query(TradeInternal).filter(
            TradeInternal.source_file_id == file_id
        ).all()
    
    def _load_cleared_trades(self, file_id: str) -> List[TradeCleared]:
        """Load cleared trades for reconciliation."""
        return self.db.query(TradeCleared).filter(
            TradeCleared.source_file_id == file_id
        ).all()
    
    def get_enhanced_exception_details(self, exception_id: str) -> Dict[str, Any]:
        """Get enhanced exception details with tick information."""
        exception = self.db.query(ReconException).filter(
            ReconException.id == exception_id
        ).first()
        
        if not exception:
            return {}
        
        details = {
            "id": str(exception.id),
            "status": exception.status,
            "keys": exception.keys,
            "internal": exception.internal,
            "cleared": exception.cleared,
            "diff": exception.diff,
            "created_at": exception.created_at.isoformat(),
            "resolution_notes": exception.resolution_notes
        }
        
        # Add enhanced tick information if available
        if exception.diff and isinstance(exception.diff, dict):
            if "details" in exception.diff:
                for detail in exception.diff["details"]:
                    if "diff_ticks" in detail:
                        details["tick_analysis"] = {
                            "diff_ticks": detail["diff_ticks"],
                            "human_description": detail.get("human_description", ""),
                            "field": detail.get("field", "")
                        }
                        break
        
        return details
    
    def get_reconciliation_summary_with_ticks(self, run_id: str) -> Dict[str, Any]:
        """Get reconciliation summary with enhanced tick metrics."""
        run = self.db.query(ReconRun).filter(ReconRun.id == run_id).first()
        
        if not run:
            return {}
        
        summary = run.summary or {}
        
        # Add tick-specific metrics
        enhanced_summary = {
            **summary,
            "tick_metrics": {
                "breaks_over_ticks": summary.get("breaks_over_ticks_total", 0),
                "perfect_matches": summary.get("perfect_matches", 0),
                "tolerance_matches": summary.get("tolerance_matches", 0),
                "products_analyzed": len(set(
                    exc.keys.get("symbol", "") for exc in 
                    self.db.query(ReconException).filter(
                        ReconException.recon_run_id == run_id
                    ).all()
                ))
            }
        }
        
        return enhanced_summary
    
    def export_exceptions_with_ticks(self, run_id: str) -> List[Dict[str, Any]]:
        """Export exceptions with enhanced tick information for CSV download."""
        exceptions = self.db.query(ReconException).filter(
            ReconException.recon_run_id == run_id
        ).all()
        
        export_data = []
        
        for exc in exceptions:
            row = {
                "exception_id": str(exc.id),
                "status": exc.status,
                "symbol": exc.keys.get("symbol", ""),
                "account": exc.keys.get("account", ""),
                "trade_date": exc.keys.get("trade_date", ""),
                "internal_price": exc.internal.get("price", "") if exc.internal else "",
                "cleared_price": exc.cleared.get("price", "") if exc.cleared else "",
                "internal_qty": exc.internal.get("qty", "") if exc.internal else "",
                "cleared_qty": exc.cleared.get("qty", "") if exc.cleared else "",
                "price_diff_absolute": "",
                "price_diff_ticks": "",
                "qty_diff": "",
                "human_description": ""
            }
            
            # Add enhanced diff information
            if exc.diff and isinstance(exc.diff, dict) and "details" in exc.diff:
                for detail in exc.diff["details"]:
                    if detail.get("field") == "price":
                        row["price_diff_absolute"] = detail.get("diff_absolute", "")
                        row["price_diff_ticks"] = detail.get("diff_ticks", "")
                        row["human_description"] = detail.get("human_description", "")
                    elif detail.get("field") == "quantity":
                        row["qty_diff"] = detail.get("diff_absolute", "")
                        if not row["human_description"]:
                            row["human_description"] = detail.get("human_description", "")
            
            export_data.append(row)
        
        return export_data
