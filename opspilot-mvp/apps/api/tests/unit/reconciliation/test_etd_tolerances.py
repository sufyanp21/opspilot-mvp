"""Tests for ETD tolerance checking with product-aware tick calculations."""

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import Mock, MagicMock

from app.reconciliation.tolerance.numeric_tolerance import (
    NumericTolerance, 
    ToleranceConfig, 
    ToleranceBreak,
    ToleranceResult
)
from app.reconciliation.engines.etd_recon_engine import ETDReconEngine, ReconConfig
from app.core.enums import PriceToleranceMode
from app.models.product import Product
from app.models.trade import TradeInternal, TradeCleared


class TestNumericTolerance:
    """Test numeric tolerance calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create ES futures product (tick size 0.25)
        self.es_product = Product(
            symbol="ES",
            exchange="CME",
            tick_size=Decimal("0.25"),
            tick_value=Decimal("12.50"),
            contract_size=50
        )
        
        # Create NQ futures product (tick size 0.25)
        self.nq_product = Product(
            symbol="NQ", 
            exchange="CME",
            tick_size=Decimal("0.25"),
            tick_value=Decimal("5.00"),
            contract_size=20
        )
    
    def test_tick_tolerance_within_limit(self):
        """Test price difference within tick tolerance passes."""
        tolerance = NumericTolerance(self.es_product)
        config = ToleranceConfig(mode=PriceToleranceMode.TICKS, max_value=1, max_ticks=1)
        
        # 0.25 difference = 1 tick, should pass with max_ticks=1
        result, break_detail = tolerance.check_price_tolerance(4150.25, 4150.50, config)
        
        assert result == ToleranceResult.MATCH
        assert break_detail is None
    
    def test_tick_tolerance_over_limit(self):
        """Test price difference over tick tolerance fails."""
        tolerance = NumericTolerance(self.es_product)
        config = ToleranceConfig(mode=PriceToleranceMode.TICKS, max_value=1, max_ticks=1)
        
        # 0.50 difference = 2 ticks, should fail with max_ticks=1
        result, break_detail = tolerance.check_price_tolerance(4150.00, 4150.50, config)
        
        assert result == ToleranceResult.BREAK
        assert break_detail is not None
        assert break_detail.diff_ticks == 2.0
        assert "2.00 ticks over tolerance (allowed 1)" in break_detail.human_description
    
    def test_tick_tolerance_exact_limit(self):
        """Test price difference exactly at tick tolerance passes."""
        tolerance = NumericTolerance(self.es_product)
        config = ToleranceConfig(mode=PriceToleranceMode.TICKS, max_value=1, max_ticks=1)
        
        # 0.25 difference = exactly 1 tick, should pass
        result, break_detail = tolerance.check_price_tolerance(4150.00, 4150.25, config)
        
        assert result == ToleranceResult.MATCH
        assert break_detail is None
    
    def test_quantity_tolerance_zero_allowed(self):
        """Test quantity difference with zero tolerance."""
        tolerance = NumericTolerance()
        config = ToleranceConfig(mode=PriceToleranceMode.ABSOLUTE, max_value=0)
        
        # Any quantity difference should fail with zero tolerance
        result, break_detail = tolerance.check_quantity_tolerance(10, 11, config)
        
        assert result == ToleranceResult.BREAK
        assert break_detail is not None
        assert break_detail.diff_absolute == 1
        assert "Quantity difference 1 exceeds tolerance 0" in break_detail.human_description
    
    def test_quantity_tolerance_exact_match(self):
        """Test exact quantity match passes."""
        tolerance = NumericTolerance()
        config = ToleranceConfig(mode=PriceToleranceMode.ABSOLUTE, max_value=0)
        
        result, break_detail = tolerance.check_quantity_tolerance(10, 10, config)
        
        assert result == ToleranceResult.MATCH
        assert break_detail is None
    
    def test_absolute_price_tolerance(self):
        """Test absolute price tolerance mode."""
        tolerance = NumericTolerance()
        config = ToleranceConfig(mode=PriceToleranceMode.ABSOLUTE, max_value=0.10)
        
        # Within tolerance
        result, break_detail = tolerance.check_price_tolerance(100.00, 100.05, config)
        assert result == ToleranceResult.MATCH
        
        # Over tolerance
        result, break_detail = tolerance.check_price_tolerance(100.00, 100.15, config)
        assert result == ToleranceResult.BREAK
        assert break_detail.diff_absolute == 0.15
    
    def test_percentage_price_tolerance(self):
        """Test percentage price tolerance mode."""
        tolerance = NumericTolerance()
        config = ToleranceConfig(mode=PriceToleranceMode.PCT, max_value=0.1)  # 0.1%
        
        # Within tolerance: 0.05% difference
        result, break_detail = tolerance.check_price_tolerance(100.00, 100.05, config)
        assert result == ToleranceResult.MATCH
        
        # Over tolerance: 0.2% difference
        result, break_detail = tolerance.check_price_tolerance(100.00, 100.20, config)
        assert result == ToleranceResult.BREAK
    
    def test_tick_tolerance_without_product_fallback(self):
        """Test tick tolerance falls back to absolute when no product provided."""
        tolerance = NumericTolerance(product=None)
        config = ToleranceConfig(mode=PriceToleranceMode.TICKS, max_value=0.25)
        
        # Should fall back to absolute tolerance
        result, break_detail = tolerance.check_price_tolerance(100.00, 100.10, config)
        assert result == ToleranceResult.MATCH  # 0.10 < 0.25
        
        result, break_detail = tolerance.check_price_tolerance(100.00, 100.30, config)
        assert result == ToleranceResult.BREAK  # 0.30 > 0.25


class TestETDReconEngine:
    """Test ETD reconciliation engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        
        # Create test configuration
        price_tolerance = ToleranceConfig(
            mode=PriceToleranceMode.TICKS, 
            max_value=1, 
            max_ticks=1
        )
        qty_tolerance = ToleranceConfig(
            mode=PriceToleranceMode.ABSOLUTE, 
            max_value=0
        )
        
        self.config = ReconConfig(
            match_keys=["trade_date", "account", "symbol"],
            price_tolerance=price_tolerance,
            quantity_tolerance=qty_tolerance
        )
        
        self.engine = ETDReconEngine(self.mock_db, self.config)
        
        # Mock product in cache
        es_product = Product(
            symbol="ES",
            exchange="CME", 
            tick_size=Decimal("0.25")
        )
        self.engine.product_cache["ES"] = es_product
    
    def create_internal_trade(self, trade_id="T001", price=4150.25, qty=10):
        """Helper to create internal trade."""
        return TradeInternal(
            trade_id=trade_id,
            account="ACC001",
            symbol="ES",
            side="BUY",
            qty=qty,
            price=Decimal(str(price)),
            trade_date=date(2024, 1, 15),
            exchange="CME"
        )
    
    def create_external_trade(self, trade_id="CLR001", price=4150.25, qty=10):
        """Helper to create external trade."""
        return TradeCleared(
            trade_id=trade_id,
            account="ACC001",
            symbol="ES",
            side="BUY",
            qty=qty,
            price=Decimal(str(price)),
            trade_date=date(2024, 1, 15),
            exchange="CME"
        )
    
    def test_perfect_match(self):
        """Test perfect match between internal and external trades."""
        internal_trades = [self.create_internal_trade()]
        external_trades = [self.create_external_trade()]
        
        matches, metrics = self.engine.reconcile(internal_trades, external_trades)
        
        assert len(matches) == 1
        assert matches[0].is_matched is True
        assert len(matches[0].tolerance_breaks) == 0
        assert metrics["perfect_matches"] == 1
        assert metrics["tolerance_matches"] == 0
    
    def test_price_within_tick_tolerance(self):
        """Test price difference within tick tolerance."""
        internal_trades = [self.create_internal_trade(price=4150.25)]
        external_trades = [self.create_external_trade(price=4150.50)]  # 1 tick difference
        
        matches, metrics = self.engine.reconcile(internal_trades, external_trades)
        
        assert len(matches) == 1
        assert matches[0].is_matched is True
        assert len(matches[0].tolerance_breaks) == 0
        assert metrics["tolerance_matches"] == 1
    
    def test_price_over_tick_tolerance(self):
        """Test price difference over tick tolerance."""
        internal_trades = [self.create_internal_trade(price=4150.00)]
        external_trades = [self.create_external_trade(price=4150.75)]  # 3 ticks difference
        
        matches, metrics = self.engine.reconcile(internal_trades, external_trades)
        
        assert len(matches) == 1
        assert matches[0].is_matched is False
        assert len(matches[0].tolerance_breaks) == 1
        
        price_break = matches[0].tolerance_breaks[0]
        assert price_break.field == "price"
        assert price_break.diff_ticks == 3.0
        assert "3.00 ticks over tolerance" in price_break.human_description
        assert metrics["breaks_over_ticks_total"] == 1
    
    def test_quantity_difference_always_breaks(self):
        """Test quantity difference always breaks with zero tolerance."""
        internal_trades = [self.create_internal_trade(qty=10)]
        external_trades = [self.create_external_trade(qty=11)]
        
        matches, metrics = self.engine.reconcile(internal_trades, external_trades)
        
        assert len(matches) == 1
        assert matches[0].is_matched is False
        assert len(matches[0].tolerance_breaks) == 1
        
        qty_break = matches[0].tolerance_breaks[0]
        assert qty_break.field == "quantity"
        assert qty_break.diff_absolute == 1
    
    def test_missing_external_trade(self):
        """Test internal trade with no external match."""
        internal_trades = [self.create_internal_trade()]
        external_trades = []
        
        matches, metrics = self.engine.reconcile(internal_trades, external_trades)
        
        assert len(matches) == 1
        assert matches[0].is_matched is False
        assert matches[0].external_trade is None
        assert metrics["missing_in_external"] == 1
    
    def test_unmatched_external_trade(self):
        """Test external trade with no internal match."""
        internal_trades = []
        external_trades = [self.create_external_trade()]
        
        matches, metrics = self.engine.reconcile(internal_trades, external_trades)
        
        assert len(matches) == 1
        assert matches[0].is_matched is False
        assert matches[0].internal_trade is None
        assert metrics["unmatched_external"] == 1
    
    def test_product_override_tolerance(self):
        """Test product-specific tolerance overrides."""
        # Configure stricter tolerance for ES
        es_price_tolerance = ToleranceConfig(
            mode=PriceToleranceMode.TICKS,
            max_value=0,
            max_ticks=0  # No tolerance allowed
        )
        
        self.config.product_overrides = {
            "ES": {"price": es_price_tolerance}
        }
        
        internal_trades = [self.create_internal_trade(price=4150.00)]
        external_trades = [self.create_external_trade(price=4150.25)]  # 1 tick difference
        
        matches, metrics = self.engine.reconcile(internal_trades, external_trades)
        
        # Should break because ES override allows 0 ticks
        assert len(matches) == 1
        assert matches[0].is_matched is False
        assert len(matches[0].tolerance_breaks) == 1
    
    def test_multiple_trades_reconciliation(self):
        """Test reconciliation with multiple trades."""
        internal_trades = [
            self.create_internal_trade("T001", 4150.00, 10),  # Perfect match
            self.create_internal_trade("T002", 4151.00, 20),  # Within tolerance
            self.create_internal_trade("T003", 4152.00, 30),  # Over tolerance
        ]
        
        external_trades = [
            self.create_external_trade("CLR001", 4150.00, 10),  # Perfect match
            self.create_external_trade("CLR002", 4151.25, 20),  # 1 tick diff
            self.create_external_trade("CLR003", 4152.75, 30),  # 3 ticks diff
        ]
        
        matches, metrics = self.engine.reconcile(internal_trades, external_trades)
        
        assert len(matches) == 3
        assert metrics["perfect_matches"] == 1
        assert metrics["tolerance_matches"] == 1
        assert metrics["breaks_over_ticks_total"] == 1
        assert metrics["total_matches"] == 2


class TestConfigurationIntegration:
    """Test configuration template integration."""
    
    def test_es_futures_template_override(self):
        """Test ES futures configuration template beats global default."""
        # This would test loading ES configuration from YAML
        # and applying product-specific tolerances
        pass  # Implementation would require file system mocking
    
    def test_template_fallback_to_default(self):
        """Test fallback to default when no product template exists."""
        pass  # Implementation would require file system mocking


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
