"""OTC reconciliation engine for economic matching of IRS and FX Forward trades."""

from typing import Dict, List, Tuple, Optional, Any
from datetime import date, timedelta
from decimal import Decimal
from dataclasses import dataclass
import logging

from app.ingestion.parsers.fpml_parser import CanonicalTrade
from app.reconciliation.tolerance.numeric_tolerance import NumericTolerance
from app.reconciliation.models.recon_result import ReconResult, ReconException, ExceptionType

logger = logging.getLogger(__name__)


@dataclass
class OTCMatchKey:
    """Composite key for OTC trade matching."""
    counterparty: str
    trade_date: date
    effective_date: Optional[date]
    maturity_date: Optional[date]
    pay_receive: Optional[str]
    notional: Optional[Decimal]
    currency: Optional[str]
    
    # Product-specific fields
    fixed_rate: Optional[Decimal] = None  # IRS
    forward_rate: Optional[Decimal] = None  # FX Forward
    currency_pair: Optional[str] = None  # FX Forward


@dataclass
class OTCToleranceConfig:
    """Tolerance configuration for OTC matching."""
    rate_tolerance_bp: Decimal = Decimal('0.5')  # 0.5 basis points
    date_tolerance_days: int = 0  # Exact date match
    notional_tolerance: Decimal = Decimal('1')  # 1 unit
    
    # Product-specific tolerances
    irs_rate_tolerance_bp: Optional[Decimal] = None
    fx_rate_tolerance_bp: Optional[Decimal] = None


@dataclass
class EconomicDifference:
    """Represents a difference in economic terms between trades."""
    field_name: str
    internal_value: Any
    external_value: Any
    difference: Any
    tolerance: Any
    is_within_tolerance: bool
    formatted_difference: str


class OTCReconEngine:
    """Reconciliation engine for OTC trades with economic matching."""
    
    def __init__(self, tolerance_config: Optional[OTCToleranceConfig] = None):
        self.tolerance_config = tolerance_config or OTCToleranceConfig()
        self.numeric_tolerance = NumericTolerance()
    
    def reconcile_trades(
        self,
        internal_trades: List[CanonicalTrade],
        external_trades: List[CanonicalTrade]
    ) -> ReconResult:
        """
        Reconcile internal vs external OTC trades with economic matching.
        
        Args:
            internal_trades: List of internal canonical trades
            external_trades: List of external canonical trades (from FpML)
            
        Returns:
            Reconciliation result with matches and exceptions
        """
        try:
            logger.info(f"Reconciling {len(internal_trades)} internal vs {len(external_trades)} external OTC trades")
            
            # Build match key indices
            internal_index = self._build_match_index(internal_trades)
            external_index = self._build_match_index(external_trades)
            
            matches = []
            exceptions = []
            
            # Find matches and economic differences
            for key, internal_trade in internal_index.items():
                external_trade = external_index.get(key)
                
                if external_trade:
                    # Found potential match - check economic terms
                    econ_diffs = self._compare_economic_terms(internal_trade, external_trade)
                    
                    if self._all_within_tolerance(econ_diffs):
                        # Perfect match
                        matches.append((internal_trade, external_trade))
                    else:
                        # Economic break
                        exception = self._create_economic_exception(
                            internal_trade, external_trade, econ_diffs
                        )
                        exceptions.append(exception)
                else:
                    # Unmatched internal trade
                    exception = ReconException(
                        exception_type=ExceptionType.MISSING_EXTERNAL,
                        trade_id=internal_trade.trade_id,
                        account=internal_trade.counterparty,
                        symbol=f"{internal_trade.product_type}",
                        side="INTERNAL",
                        internal_qty=self._get_trade_notional(internal_trade),
                        external_qty=None,
                        internal_price=self._get_trade_rate(internal_trade),
                        external_price=None,
                        difference_summary=f"Missing external confirmation for {internal_trade.product_type} trade",
                        raw_internal_data=self._trade_to_dict(internal_trade),
                        raw_external_data=None
                    )
                    exceptions.append(exception)
            
            # Find unmatched external trades
            for key, external_trade in external_index.items():
                if key not in internal_index:
                    exception = ReconException(
                        exception_type=ExceptionType.MISSING_INTERNAL,
                        trade_id=external_trade.trade_id,
                        account=external_trade.counterparty,
                        symbol=f"{external_trade.product_type}",
                        side="EXTERNAL",
                        internal_qty=None,
                        external_qty=self._get_trade_notional(external_trade),
                        internal_price=None,
                        external_price=self._get_trade_rate(external_trade),
                        difference_summary=f"Missing internal trade for {external_trade.product_type} confirmation",
                        raw_internal_data=None,
                        raw_external_data=self._trade_to_dict(external_trade)
                    )
                    exceptions.append(exception)
            
            result = ReconResult(
                total_internal=len(internal_trades),
                total_external=len(external_trades),
                matched_count=len(matches),
                exception_count=len(exceptions),
                exceptions=exceptions,
                summary_stats={
                    "irs_trades": len([t for t in internal_trades if t.product_type == "IRS"]),
                    "fx_trades": len([t for t in internal_trades if t.product_type == "FX_FWD"]),
                    "economic_breaks": len([e for e in exceptions if e.exception_type == ExceptionType.PRICE_BREAK]),
                    "missing_confirmations": len([e for e in exceptions if e.exception_type == ExceptionType.MISSING_EXTERNAL]),
                    "unexpected_confirmations": len([e for e in exceptions if e.exception_type == ExceptionType.MISSING_INTERNAL])
                }
            )
            
            logger.info(f"OTC reconciliation complete: {len(matches)} matches, {len(exceptions)} exceptions")
            return result
            
        except Exception as e:
            logger.error(f"Error in OTC reconciliation: {e}")
            raise
    
    def _build_match_index(self, trades: List[CanonicalTrade]) -> Dict[OTCMatchKey, CanonicalTrade]:
        """Build index of trades by match key."""
        index = {}
        
        for trade in trades:
            try:
                key = self._create_match_key(trade)
                if key in index:
                    logger.warning(f"Duplicate match key found for trade {trade.trade_id}")
                index[key] = trade
            except Exception as e:
                logger.warning(f"Could not create match key for trade {trade.trade_id}: {e}")
                continue
        
        return index
    
    def _create_match_key(self, trade: CanonicalTrade) -> OTCMatchKey:
        """Create composite match key for trade."""
        if trade.product_type == "IRS":
            return OTCMatchKey(
                counterparty=trade.counterparty,
                trade_date=trade.trade_date,
                effective_date=trade.effective_date,
                maturity_date=trade.maturity_date,
                pay_receive=trade.pay_receive,
                notional=trade.notional,
                currency=trade.currency,
                fixed_rate=trade.fixed_rate
            )
        elif trade.product_type == "FX_FWD":
            # Create normalized currency pair (alphabetical order)
            currency_pair = None
            if trade.currency1 and trade.currency2:
                currencies = sorted([trade.currency1, trade.currency2])
                currency_pair = f"{currencies[0]}/{currencies[1]}"
            
            return OTCMatchKey(
                counterparty=trade.counterparty,
                trade_date=trade.trade_date,
                effective_date=trade.value_date,  # Use value_date as effective_date for FX
                maturity_date=trade.value_date,
                pay_receive=None,  # Not applicable for FX
                notional=trade.notional1,  # Use primary notional
                currency=trade.currency1,
                forward_rate=trade.forward_rate,
                currency_pair=currency_pair
            )
        else:
            raise ValueError(f"Unsupported product type: {trade.product_type}")
    
    def _compare_economic_terms(
        self, 
        internal_trade: CanonicalTrade, 
        external_trade: CanonicalTrade
    ) -> List[EconomicDifference]:
        """Compare economic terms between internal and external trades."""
        differences = []
        
        if internal_trade.product_type != external_trade.product_type:
            differences.append(EconomicDifference(
                field_name="product_type",
                internal_value=internal_trade.product_type,
                external_value=external_trade.product_type,
                difference="Product type mismatch",
                tolerance="Exact match required",
                is_within_tolerance=False,
                formatted_difference=f"{internal_trade.product_type} vs {external_trade.product_type}"
            ))
            return differences  # Cannot compare further if product types differ
        
        if internal_trade.product_type == "IRS":
            differences.extend(self._compare_irs_terms(internal_trade, external_trade))
        elif internal_trade.product_type == "FX_FWD":
            differences.extend(self._compare_fx_terms(internal_trade, external_trade))
        
        return differences
    
    def _compare_irs_terms(
        self, 
        internal_trade: CanonicalTrade, 
        external_trade: CanonicalTrade
    ) -> List[EconomicDifference]:
        """Compare IRS-specific economic terms."""
        differences = []
        
        # Compare fixed rate (in basis points)
        if internal_trade.fixed_rate is not None and external_trade.fixed_rate is not None:
            rate_diff_bp = abs(internal_trade.fixed_rate - external_trade.fixed_rate) * 10000
            rate_tolerance = self.tolerance_config.irs_rate_tolerance_bp or self.tolerance_config.rate_tolerance_bp
            
            differences.append(EconomicDifference(
                field_name="fixed_rate",
                internal_value=internal_trade.fixed_rate,
                external_value=external_trade.fixed_rate,
                difference=rate_diff_bp,
                tolerance=rate_tolerance,
                is_within_tolerance=rate_diff_bp <= rate_tolerance,
                formatted_difference=f"{rate_diff_bp:.1f} bp"
            ))
        
        # Compare notional
        if internal_trade.notional is not None and external_trade.notional is not None:
            notional_diff = abs(internal_trade.notional - external_trade.notional)
            
            differences.append(EconomicDifference(
                field_name="notional",
                internal_value=internal_trade.notional,
                external_value=external_trade.notional,
                difference=notional_diff,
                tolerance=self.tolerance_config.notional_tolerance,
                is_within_tolerance=notional_diff <= self.tolerance_config.notional_tolerance,
                formatted_difference=f"{internal_trade.currency} {notional_diff:,.0f}"
            ))
        
        # Compare dates
        differences.extend(self._compare_dates(internal_trade, external_trade))
        
        # Compare other IRS fields
        self._compare_field(differences, "pay_receive", internal_trade.pay_receive, external_trade.pay_receive)
        self._compare_field(differences, "currency", internal_trade.currency, external_trade.currency)
        self._compare_field(differences, "floating_index", internal_trade.floating_index, external_trade.floating_index)
        
        return differences
    
    def _compare_fx_terms(
        self, 
        internal_trade: CanonicalTrade, 
        external_trade: CanonicalTrade
    ) -> List[EconomicDifference]:
        """Compare FX Forward-specific economic terms."""
        differences = []
        
        # Compare forward rate (in basis points if applicable)
        if internal_trade.forward_rate is not None and external_trade.forward_rate is not None:
            rate_diff_pct = abs(internal_trade.forward_rate - external_trade.forward_rate) / internal_trade.forward_rate * 100
            rate_diff_bp = rate_diff_pct * 100  # Convert to basis points
            rate_tolerance = self.tolerance_config.fx_rate_tolerance_bp or self.tolerance_config.rate_tolerance_bp
            
            differences.append(EconomicDifference(
                field_name="forward_rate",
                internal_value=internal_trade.forward_rate,
                external_value=external_trade.forward_rate,
                difference=rate_diff_bp,
                tolerance=rate_tolerance,
                is_within_tolerance=rate_diff_bp <= rate_tolerance,
                formatted_difference=f"{rate_diff_bp:.1f} bp ({rate_diff_pct:.3f}%)"
            ))
        
        # Compare notionals
        if internal_trade.notional1 is not None and external_trade.notional1 is not None:
            notional_diff = abs(internal_trade.notional1 - external_trade.notional1)
            
            differences.append(EconomicDifference(
                field_name="notional1",
                internal_value=internal_trade.notional1,
                external_value=external_trade.notional1,
                difference=notional_diff,
                tolerance=self.tolerance_config.notional_tolerance,
                is_within_tolerance=notional_diff <= self.tolerance_config.notional_tolerance,
                formatted_difference=f"{internal_trade.currency1} {notional_diff:,.0f}"
            ))
        
        # Compare dates
        differences.extend(self._compare_dates(internal_trade, external_trade))
        
        # Compare currencies
        self._compare_field(differences, "currency1", internal_trade.currency1, external_trade.currency1)
        self._compare_field(differences, "currency2", internal_trade.currency2, external_trade.currency2)
        
        return differences
    
    def _compare_dates(
        self, 
        internal_trade: CanonicalTrade, 
        external_trade: CanonicalTrade
    ) -> List[EconomicDifference]:
        """Compare date fields with tolerance."""
        differences = []
        
        date_fields = [
            ("trade_date", internal_trade.trade_date, external_trade.trade_date),
            ("effective_date", internal_trade.effective_date, external_trade.effective_date),
            ("maturity_date", internal_trade.maturity_date, external_trade.maturity_date),
            ("value_date", internal_trade.value_date, external_trade.value_date)
        ]
        
        for field_name, internal_date, external_date in date_fields:
            if internal_date is not None and external_date is not None:
                date_diff_days = abs((internal_date - external_date).days)
                
                differences.append(EconomicDifference(
                    field_name=field_name,
                    internal_value=internal_date,
                    external_value=external_date,
                    difference=date_diff_days,
                    tolerance=self.tolerance_config.date_tolerance_days,
                    is_within_tolerance=date_diff_days <= self.tolerance_config.date_tolerance_days,
                    formatted_difference=f"{date_diff_days} days"
                ))
        
        return differences
    
    def _compare_field(
        self, 
        differences: List[EconomicDifference], 
        field_name: str, 
        internal_value: Any, 
        external_value: Any
    ):
        """Compare generic field values."""
        if internal_value is not None and external_value is not None:
            is_match = internal_value == external_value
            
            differences.append(EconomicDifference(
                field_name=field_name,
                internal_value=internal_value,
                external_value=external_value,
                difference="Match" if is_match else "Mismatch",
                tolerance="Exact match required",
                is_within_tolerance=is_match,
                formatted_difference=f"{internal_value} vs {external_value}" if not is_match else "Match"
            ))
    
    def _all_within_tolerance(self, differences: List[EconomicDifference]) -> bool:
        """Check if all differences are within tolerance."""
        return all(diff.is_within_tolerance for diff in differences)
    
    def _create_economic_exception(
        self,
        internal_trade: CanonicalTrade,
        external_trade: CanonicalTrade,
        differences: List[EconomicDifference]
    ) -> ReconException:
        """Create exception for economic differences."""
        
        # Categorize the primary issue
        rate_breaks = [d for d in differences if 'rate' in d.field_name and not d.is_within_tolerance]
        date_breaks = [d for d in differences if 'date' in d.field_name and not d.is_within_tolerance]
        notional_breaks = [d for d in differences if 'notional' in d.field_name and not d.is_within_tolerance]
        
        if rate_breaks:
            exception_type = ExceptionType.PRICE_BREAK
            primary_diff = rate_breaks[0]
        elif notional_breaks:
            exception_type = ExceptionType.QTY_BREAK
            primary_diff = notional_breaks[0]
        else:
            exception_type = ExceptionType.OTHER
            primary_diff = next((d for d in differences if not d.is_within_tolerance), differences[0])
        
        # Create formatted summary
        break_summaries = []
        for diff in differences:
            if not diff.is_within_tolerance:
                break_summaries.append(f"{diff.field_name}: {diff.formatted_difference}")
        
        difference_summary = f"{internal_trade.product_type} economic breaks: {'; '.join(break_summaries)}"
        
        return ReconException(
            exception_type=exception_type,
            trade_id=internal_trade.trade_id,
            account=internal_trade.counterparty,
            symbol=f"{internal_trade.product_type}",
            side="BOTH",
            internal_qty=self._get_trade_notional(internal_trade),
            external_qty=self._get_trade_notional(external_trade),
            internal_price=self._get_trade_rate(internal_trade),
            external_price=self._get_trade_rate(external_trade),
            difference_summary=difference_summary,
            raw_internal_data=self._trade_to_dict(internal_trade),
            raw_external_data=self._trade_to_dict(external_trade),
            additional_details={
                "economic_differences": [
                    {
                        "field": diff.field_name,
                        "internal": str(diff.internal_value),
                        "external": str(diff.external_value),
                        "difference": diff.formatted_difference,
                        "within_tolerance": diff.is_within_tolerance
                    }
                    for diff in differences
                ]
            }
        )
    
    def _get_trade_notional(self, trade: CanonicalTrade) -> Optional[float]:
        """Get primary notional amount from trade."""
        if trade.notional:
            return float(trade.notional)
        elif trade.notional1:
            return float(trade.notional1)
        return None
    
    def _get_trade_rate(self, trade: CanonicalTrade) -> Optional[float]:
        """Get primary rate from trade."""
        if trade.fixed_rate:
            return float(trade.fixed_rate)
        elif trade.forward_rate:
            return float(trade.forward_rate)
        return None
    
    def _trade_to_dict(self, trade: CanonicalTrade) -> Dict[str, Any]:
        """Convert trade to dictionary for storage."""
        return {
            "trade_id": trade.trade_id,
            "trade_date": trade.trade_date.isoformat() if trade.trade_date else None,
            "counterparty": trade.counterparty,
            "product_type": trade.product_type,
            "uti": trade.uti,
            "notional": float(trade.notional) if trade.notional else None,
            "currency": trade.currency,
            "effective_date": trade.effective_date.isoformat() if trade.effective_date else None,
            "maturity_date": trade.maturity_date.isoformat() if trade.maturity_date else None,
            "fixed_rate": float(trade.fixed_rate) if trade.fixed_rate else None,
            "floating_index": trade.floating_index,
            "floating_spread": float(trade.floating_spread) if trade.floating_spread else None,
            "pay_receive": trade.pay_receive,
            "day_count": trade.day_count,
            "currency1": trade.currency1,
            "currency2": trade.currency2,
            "notional1": float(trade.notional1) if trade.notional1 else None,
            "notional2": float(trade.notional2) if trade.notional2 else None,
            "forward_rate": float(trade.forward_rate) if trade.forward_rate else None,
            "value_date": trade.value_date.isoformat() if trade.value_date else None,
            "source_file": trade.source_file,
            "parsed_at": trade.parsed_at.isoformat() if trade.parsed_at else None
        }
