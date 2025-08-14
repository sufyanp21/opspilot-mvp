"""Numeric tolerance checking with product-aware tick calculations."""

from typing import Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import logging

from app.core.enums import PriceToleranceMode, ToleranceResult
from app.models.product import Product

logger = logging.getLogger(__name__)


class ToleranceConfig:
    """Configuration for tolerance checking."""
    
    def __init__(self, mode: PriceToleranceMode, max_value: float, max_ticks: Optional[int] = None):
        self.mode = mode
        self.max_value = max_value
        self.max_ticks = max_ticks or int(max_value)


class ToleranceBreak:
    """Details of a tolerance break."""
    
    def __init__(
        self,
        field: str,
        internal_value: Any,
        external_value: Any,
        diff_absolute: float,
        diff_ticks: Optional[float] = None,
        allowed_tolerance: float = 0,
        human_description: str = ""
    ):
        self.field = field
        self.internal_value = internal_value
        self.external_value = external_value
        self.diff_absolute = diff_absolute
        self.diff_ticks = diff_ticks
        self.allowed_tolerance = allowed_tolerance
        self.human_description = human_description


class NumericTolerance:
    """Handles numeric tolerance checking with product-aware calculations."""
    
    def __init__(self, product: Optional[Product] = None):
        self.product = product
        
    def check_price_tolerance(
        self,
        internal_price: float,
        external_price: float,
        config: ToleranceConfig
    ) -> Tuple[ToleranceResult, Optional[ToleranceBreak]]:
        """
        Check price tolerance using specified mode.
        
        Args:
            internal_price: Price from internal system
            external_price: Price from external system
            config: Tolerance configuration
            
        Returns:
            Tuple of (result, break_details)
        """
        diff_absolute = abs(float(internal_price) - float(external_price))
        
        if config.mode == PriceToleranceMode.ABSOLUTE:
            return self._check_absolute_tolerance(
                internal_price, external_price, diff_absolute, config
            )
        elif config.mode == PriceToleranceMode.PCT:
            return self._check_percentage_tolerance(
                internal_price, external_price, diff_absolute, config
            )
        elif config.mode == PriceToleranceMode.TICKS:
            return self._check_tick_tolerance(
                internal_price, external_price, diff_absolute, config
            )
        else:
            raise ValueError(f"Unsupported tolerance mode: {config.mode}")
    
    def check_quantity_tolerance(
        self,
        internal_qty: int,
        external_qty: int,
        config: ToleranceConfig
    ) -> Tuple[ToleranceResult, Optional[ToleranceBreak]]:
        """Check quantity tolerance (typically zero tolerance)."""
        diff_absolute = abs(int(internal_qty) - int(external_qty))
        
        if diff_absolute <= config.max_value:
            return ToleranceResult.MATCH, None
        
        break_detail = ToleranceBreak(
            field="quantity",
            internal_value=internal_qty,
            external_value=external_qty,
            diff_absolute=diff_absolute,
            allowed_tolerance=config.max_value,
            human_description=f"Quantity difference {diff_absolute} exceeds tolerance {config.max_value}"
        )
        
        return ToleranceResult.BREAK, break_detail
    
    def _check_absolute_tolerance(
        self,
        internal_price: float,
        external_price: float,
        diff_absolute: float,
        config: ToleranceConfig
    ) -> Tuple[ToleranceResult, Optional[ToleranceBreak]]:
        """Check absolute price tolerance."""
        if diff_absolute <= config.max_value:
            return ToleranceResult.MATCH, None
        
        break_detail = ToleranceBreak(
            field="price",
            internal_value=internal_price,
            external_value=external_price,
            diff_absolute=diff_absolute,
            allowed_tolerance=config.max_value,
            human_description=f"Price difference ${diff_absolute:.4f} exceeds tolerance ${config.max_value:.4f}"
        )
        
        return ToleranceResult.BREAK, break_detail
    
    def _check_percentage_tolerance(
        self,
        internal_price: float,
        external_price: float,
        diff_absolute: float,
        config: ToleranceConfig
    ) -> Tuple[ToleranceResult, Optional[ToleranceBreak]]:
        """Check percentage price tolerance."""
        base_price = max(abs(float(internal_price)), abs(float(external_price)))
        if base_price == 0:
            # Handle zero price case
            return (ToleranceResult.MATCH, None) if diff_absolute == 0 else (ToleranceResult.BREAK, None)
        
        diff_pct = (diff_absolute / base_price) * 100
        
        if diff_pct <= config.max_value:
            return ToleranceResult.MATCH, None
        
        break_detail = ToleranceBreak(
            field="price",
            internal_value=internal_price,
            external_value=external_price,
            diff_absolute=diff_absolute,
            allowed_tolerance=config.max_value,
            human_description=f"Price difference {diff_pct:.2f}% exceeds tolerance {config.max_value:.2f}%"
        )
        
        return ToleranceResult.BREAK, break_detail
    
    def _check_tick_tolerance(
        self,
        internal_price: float,
        external_price: float,
        diff_absolute: float,
        config: ToleranceConfig
    ) -> Tuple[ToleranceResult, Optional[ToleranceBreak]]:
        """Check tick-based price tolerance."""
        if not self.product:
            logger.warning("No product provided for tick tolerance check, falling back to absolute")
            return self._check_absolute_tolerance(internal_price, external_price, diff_absolute, config)
        
        # Calculate difference in ticks
        diff_ticks = diff_absolute / float(self.product.tick_size)
        max_ticks = config.max_ticks or config.max_value
        
        if diff_ticks <= max_ticks:
            return ToleranceResult.MATCH, None
        
        # Create detailed break information
        break_detail = ToleranceBreak(
            field="price",
            internal_value=internal_price,
            external_value=external_price,
            diff_absolute=diff_absolute,
            diff_ticks=diff_ticks,
            allowed_tolerance=max_ticks,
            human_description=f"{diff_ticks:.2f} ticks over tolerance (allowed {max_ticks})"
        )
        
        return ToleranceResult.BREAK, break_detail
    
    def format_break_summary(self, breaks: list[ToleranceBreak]) -> Dict[str, Any]:
        """Format tolerance breaks for reporting."""
        summary = {
            "total_breaks": len(breaks),
            "breaks_by_field": {},
            "details": []
        }
        
        for break_detail in breaks:
            # Count by field
            field = break_detail.field
            if field not in summary["breaks_by_field"]:
                summary["breaks_by_field"][field] = 0
            summary["breaks_by_field"][field] += 1
            
            # Add detailed information
            detail = {
                "field": break_detail.field,
                "internal_value": break_detail.internal_value,
                "external_value": break_detail.external_value,
                "diff_absolute": break_detail.diff_absolute,
                "allowed_tolerance": break_detail.allowed_tolerance,
                "human_description": break_detail.human_description
            }
            
            if break_detail.diff_ticks is not None:
                detail["diff_ticks"] = break_detail.diff_ticks
            
            summary["details"].append(detail)
        
        return summary
