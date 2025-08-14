"""ETD (Exchange Traded Derivatives) reconciliation engine with product-aware tolerances."""

from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.reconciliation.tolerance.numeric_tolerance import (
    NumericTolerance, 
    ToleranceConfig, 
    ToleranceBreak,
    ToleranceResult
)
from app.core.enums import PriceToleranceMode
from app.models.product import Product
from app.models.trade import TradeInternal, TradeCleared
from app.models.recon import ReconException, ExceptionStatus

logger = logging.getLogger(__name__)


@dataclass
class ReconConfig:
    """Configuration for reconciliation run."""
    match_keys: List[str]
    price_tolerance: ToleranceConfig
    quantity_tolerance: ToleranceConfig
    product_overrides: Dict[str, Dict[str, ToleranceConfig]] = None
    
    def __post_init__(self):
        if self.product_overrides is None:
            self.product_overrides = {}


@dataclass
class ReconMatch:
    """Result of a reconciliation match attempt."""
    internal_trade: TradeInternal
    external_trade: Optional[TradeCleared]
    is_matched: bool
    tolerance_breaks: List[ToleranceBreak]
    match_keys: Dict[str, Any]


class ETDReconEngine:
    """Enhanced reconciliation engine for Exchange Traded Derivatives."""
    
    def __init__(self, db: Session, config: ReconConfig):
        self.db = db
        self.config = config
        self.product_cache: Dict[str, Product] = {}
        self.metrics = {
            "total_internal": 0,
            "total_external": 0,
            "perfect_matches": 0,
            "tolerance_matches": 0,
            "breaks_over_ticks_total": 0,
            "missing_in_external": 0,
            "missing_in_internal": 0,
            "unmatched_external": 0
        }
    
    def reconcile(
        self, 
        internal_trades: List[TradeInternal], 
        external_trades: List[TradeCleared]
    ) -> Tuple[List[ReconMatch], Dict[str, Any]]:
        """
        Perform reconciliation with product-aware tolerances.
        
        Args:
            internal_trades: List of internal trades
            external_trades: List of external trades
            
        Returns:
            Tuple of (matches, summary_metrics)
        """
        logger.info(f"Starting ETD reconciliation: {len(internal_trades)} internal, {len(external_trades)} external")
        
        self.metrics["total_internal"] = len(internal_trades)
        self.metrics["total_external"] = len(external_trades)
        
        # Pre-load products for all symbols
        self._preload_products(internal_trades, external_trades)
        
        # Create lookup maps
        external_lookup = self._create_external_lookup(external_trades)
        matched_external_ids = set()
        
        matches = []
        
        # Process each internal trade
        for internal_trade in internal_trades:
            match_result = self._match_internal_trade(
                internal_trade, 
                external_lookup, 
                matched_external_ids
            )
            matches.append(match_result)
            
            if match_result.external_trade:
                matched_external_ids.add(match_result.external_trade.id)
        
        # Find unmatched external trades
        unmatched_external = [
            trade for trade in external_trades 
            if trade.id not in matched_external_ids
        ]
        
        # Create matches for unmatched external trades
        for external_trade in unmatched_external:
            match_keys = self._extract_match_keys(external_trade, is_external=True)
            match_result = ReconMatch(
                internal_trade=None,
                external_trade=external_trade,
                is_matched=False,
                tolerance_breaks=[],
                match_keys=match_keys
            )
            matches.append(match_result)
        
        self.metrics["unmatched_external"] = len(unmatched_external)
        
        # Calculate final metrics
        self._calculate_final_metrics(matches)
        
        logger.info(f"Reconciliation complete: {self.metrics}")
        
        return matches, self.metrics
    
    def _preload_products(self, internal_trades: List[TradeInternal], external_trades: List[TradeCleared]):
        """Pre-load product information for all symbols."""
        symbols = set()
        
        for trade in internal_trades:
            symbols.add(trade.symbol)
        
        for trade in external_trades:
            symbols.add(trade.symbol)
        
        # Load products from database
        products = self.db.query(Product).filter(Product.symbol.in_(symbols)).all()
        
        for product in products:
            self.product_cache[product.symbol] = product
        
        # Log missing products
        missing_symbols = symbols - set(self.product_cache.keys())
        if missing_symbols:
            logger.warning(f"Missing product definitions for symbols: {missing_symbols}")
    
    def _create_external_lookup(self, external_trades: List[TradeCleared]) -> Dict[str, List[TradeCleared]]:
        """Create lookup map for external trades by match keys."""
        lookup = {}
        
        for trade in external_trades:
            key = self._create_match_key(trade, is_external=True)
            if key not in lookup:
                lookup[key] = []
            lookup[key].append(trade)
        
        return lookup
    
    def _match_internal_trade(
        self, 
        internal_trade: TradeInternal, 
        external_lookup: Dict[str, List[TradeCleared]],
        matched_external_ids: set
    ) -> ReconMatch:
        """Match a single internal trade against external trades."""
        match_key = self._create_match_key(internal_trade, is_external=False)
        match_keys_dict = self._extract_match_keys(internal_trade, is_external=False)
        
        # Find potential external matches
        potential_matches = external_lookup.get(match_key, [])
        available_matches = [
            trade for trade in potential_matches 
            if trade.id not in matched_external_ids
        ]
        
        if not available_matches:
            # No external match found
            self.metrics["missing_in_external"] += 1
            return ReconMatch(
                internal_trade=internal_trade,
                external_trade=None,
                is_matched=False,
                tolerance_breaks=[],
                match_keys=match_keys_dict
            )
        
        # Use first available match (could be enhanced with best-match logic)
        external_trade = available_matches[0]
        
        # Check tolerances
        tolerance_breaks = self._check_tolerances(internal_trade, external_trade)
        is_matched = len(tolerance_breaks) == 0
        
        if is_matched:
            if self._is_perfect_match(internal_trade, external_trade):
                self.metrics["perfect_matches"] += 1
            else:
                self.metrics["tolerance_matches"] += 1
        else:
            # Count tick-based breaks
            tick_breaks = [b for b in tolerance_breaks if b.diff_ticks is not None]
            self.metrics["breaks_over_ticks_total"] += len(tick_breaks)
        
        return ReconMatch(
            internal_trade=internal_trade,
            external_trade=external_trade,
            is_matched=is_matched,
            tolerance_breaks=tolerance_breaks,
            match_keys=match_keys_dict
        )
    
    def _create_match_key(self, trade: Any, is_external: bool) -> str:
        """Create composite match key for trade."""
        key_parts = []
        
        for field in self.config.match_keys:
            value = getattr(trade, field, None)
            if value is not None:
                key_parts.append(str(value))
            else:
                key_parts.append("")
        
        return "|".join(key_parts)
    
    def _extract_match_keys(self, trade: Any, is_external: bool) -> Dict[str, Any]:
        """Extract match key values as dictionary."""
        keys = {}
        
        for field in self.config.match_keys:
            keys[field] = getattr(trade, field, None)
        
        return keys
    
    def _check_tolerances(
        self, 
        internal_trade: TradeInternal, 
        external_trade: TradeCleared
    ) -> List[ToleranceBreak]:
        """Check all configured tolerances between trades."""
        breaks = []
        
        # Get product for tick-aware calculations
        product = self.product_cache.get(internal_trade.symbol)
        tolerance_checker = NumericTolerance(product)
        
        # Get product-specific overrides if available
        symbol = internal_trade.symbol
        overrides = self.config.product_overrides.get(symbol, {})
        
        # Check price tolerance
        price_config = overrides.get("price", self.config.price_tolerance)
        price_result, price_break = tolerance_checker.check_price_tolerance(
            float(internal_trade.price),
            float(external_trade.price),
            price_config
        )
        
        if price_result == ToleranceResult.BREAK and price_break:
            breaks.append(price_break)
        
        # Check quantity tolerance
        qty_config = overrides.get("quantity", self.config.quantity_tolerance)
        qty_result, qty_break = tolerance_checker.check_quantity_tolerance(
            internal_trade.qty,
            external_trade.qty,
            qty_config
        )
        
        if qty_result == ToleranceResult.BREAK and qty_break:
            breaks.append(qty_break)
        
        return breaks
    
    def _is_perfect_match(self, internal_trade: TradeInternal, external_trade: TradeCleared) -> bool:
        """Check if trades match exactly (no tolerance needed)."""
        return (
            float(internal_trade.price) == float(external_trade.price) and
            internal_trade.qty == external_trade.qty
        )
    
    def _calculate_final_metrics(self, matches: List[ReconMatch]):
        """Calculate final reconciliation metrics."""
        matched_count = sum(1 for match in matches if match.is_matched)
        total_trades = max(self.metrics["total_internal"], self.metrics["total_external"])
        
        if total_trades > 0:
            self.metrics["match_rate_pct"] = (matched_count / total_trades) * 100
        else:
            self.metrics["match_rate_pct"] = 100.0
        
        self.metrics["total_matches"] = matched_count
        self.metrics["total_breaks"] = len(matches) - matched_count
    
    def create_exceptions(self, matches: List[ReconMatch], recon_run_id: str) -> List[ReconException]:
        """Create exception records for failed matches."""
        exceptions = []
        
        for match in matches:
            if not match.is_matched:
                # Determine exception type
                if match.internal_trade and not match.external_trade:
                    status = ExceptionStatus.OPEN
                    diff_data = {"status": "missing_in_external"}
                elif match.external_trade and not match.internal_trade:
                    status = ExceptionStatus.OPEN
                    diff_data = {"status": "missing_in_internal"}
                else:
                    status = ExceptionStatus.OPEN
                    diff_data = self._format_tolerance_breaks(match.tolerance_breaks)
                
                exception = ReconException(
                    recon_run_id=recon_run_id,
                    status=status,
                    keys=match.match_keys,
                    internal=self._trade_to_dict(match.internal_trade) if match.internal_trade else None,
                    cleared=self._trade_to_dict(match.external_trade) if match.external_trade else None,
                    diff=diff_data
                )
                
                exceptions.append(exception)
        
        return exceptions
    
    def _format_tolerance_breaks(self, breaks: List[ToleranceBreak]) -> Dict[str, Any]:
        """Format tolerance breaks for exception storage."""
        if not breaks:
            return {}
        
        tolerance_checker = NumericTolerance()
        return tolerance_checker.format_break_summary(breaks)
    
    def _trade_to_dict(self, trade: Any) -> Dict[str, Any]:
        """Convert trade object to dictionary for storage."""
        if not trade:
            return {}
        
        return {
            "trade_id": trade.trade_id,
            "account": trade.account,
            "symbol": trade.symbol,
            "side": trade.side,
            "qty": trade.qty,
            "price": float(trade.price),
            "trade_date": trade.trade_date.isoformat() if trade.trade_date else None,
            "exchange": trade.exchange,
            "clearing_ref": trade.clearing_ref
        }
