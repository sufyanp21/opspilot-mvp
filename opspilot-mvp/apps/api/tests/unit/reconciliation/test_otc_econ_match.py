"""Unit tests for OTC economic matching reconciliation."""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from app.ingestion.parsers.fpml_parser import CanonicalTrade
from app.reconciliation.engines.otc_recon_engine import (
    OTCReconEngine,
    OTCToleranceConfig,
    OTCMatchKey,
    EconomicDifference
)
from app.reconciliation.models.recon_result import ExceptionType


class TestOTCReconEngine:
    """Test OTC reconciliation engine functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tolerance_config = OTCToleranceConfig(
            rate_tolerance_bp=Decimal('0.5'),
            notional_tolerance=Decimal('1'),
            date_tolerance_days=0
        )
        self.engine = OTCReconEngine(self.tolerance_config)
        
        # Create test IRS trades
        self.internal_irs = CanonicalTrade(
            trade_id="IRS001",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="IRS",
            notional=Decimal("10000000"),
            currency="USD",
            effective_date=date(2024, 1, 17),
            maturity_date=date(2029, 1, 17),
            fixed_rate=Decimal("0.035"),
            floating_index="USD-LIBOR-BBA",
            floating_spread=Decimal("0.0025"),
            pay_receive="PAY",
            day_count="ACT/360"
        )
        
        self.external_irs_match = CanonicalTrade(
            trade_id="IRS001_CONF",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="IRS",
            notional=Decimal("10000000"),
            currency="USD",
            effective_date=date(2024, 1, 17),
            maturity_date=date(2029, 1, 17),
            fixed_rate=Decimal("0.035"),  # Exact match
            floating_index="USD-LIBOR-BBA",
            floating_spread=Decimal("0.0025"),
            pay_receive="PAY",
            day_count="ACT/360"
        )
        
        # Create test FX trades
        self.internal_fx = CanonicalTrade(
            trade_id="FX001",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="FX_FWD",
            currency1="USD",
            currency2="EUR",
            notional1=Decimal("1000000"),
            notional2=Decimal("920000"),
            forward_rate=Decimal("0.92"),
            value_date=date(2024, 1, 17)
        )
        
        self.external_fx_match = CanonicalTrade(
            trade_id="FX001_CONF",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="FX_FWD",
            currency1="USD",
            currency2="EUR",
            notional1=Decimal("1000000"),
            notional2=Decimal("920000"),
            forward_rate=Decimal("0.92"),
            value_date=date(2024, 1, 17)
        )
    
    def test_perfect_irs_match(self):
        """Test perfect IRS trade matching."""
        internal_trades = [self.internal_irs]
        external_trades = [self.external_irs_match]
        
        result = self.engine.reconcile_trades(internal_trades, external_trades)
        
        assert result.total_internal == 1
        assert result.total_external == 1
        assert result.matched_count == 1
        assert result.exception_count == 0
        assert len(result.exceptions) == 0
    
    def test_irs_rate_break_within_tolerance(self):
        """Test IRS rate difference within tolerance."""
        # Create external trade with rate difference within tolerance (0.3 bp)
        external_irs_close = CanonicalTrade(
            trade_id="IRS001_CONF",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="IRS",
            notional=Decimal("10000000"),
            currency="USD",
            effective_date=date(2024, 1, 17),
            maturity_date=date(2029, 1, 17),
            fixed_rate=Decimal("0.0350030"),  # 0.3 bp higher
            floating_index="USD-LIBOR-BBA",
            floating_spread=Decimal("0.0025"),
            pay_receive="PAY",
            day_count="ACT/360"
        )
        
        internal_trades = [self.internal_irs]
        external_trades = [external_irs_close]
        
        result = self.engine.reconcile_trades(internal_trades, external_trades)
        
        assert result.matched_count == 1
        assert result.exception_count == 0
    
    def test_irs_rate_break_exceeds_tolerance(self):
        """Test IRS rate difference exceeding tolerance."""
        # Create external trade with rate difference exceeding tolerance (1.2 bp)
        external_irs_break = CanonicalTrade(
            trade_id="IRS001_CONF",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="IRS",
            notional=Decimal("10000000"),
            currency="USD",
            effective_date=date(2024, 1, 17),
            maturity_date=date(2029, 1, 17),
            fixed_rate=Decimal("0.0350120"),  # 1.2 bp higher
            floating_index="USD-LIBOR-BBA",
            floating_spread=Decimal("0.0025"),
            pay_receive="PAY",
            day_count="ACT/360"
        )
        
        internal_trades = [self.internal_irs]
        external_trades = [external_irs_break]
        
        result = self.engine.reconcile_trades(internal_trades, external_trades)
        
        assert result.matched_count == 0
        assert result.exception_count == 1
        
        exception = result.exceptions[0]
        assert exception.exception_type == ExceptionType.PRICE_BREAK
        assert exception.trade_id == "IRS001"
        assert "1.2 bp" in exception.difference_summary
    
    def test_perfect_fx_match(self):
        """Test perfect FX Forward trade matching."""
        internal_trades = [self.internal_fx]
        external_trades = [self.external_fx_match]
        
        result = self.engine.reconcile_trades(internal_trades, external_trades)
        
        assert result.total_internal == 1
        assert result.total_external == 1
        assert result.matched_count == 1
        assert result.exception_count == 0
    
    def test_fx_rate_break_exceeds_tolerance(self):
        """Test FX Forward rate difference exceeding tolerance."""
        # Create external trade with significant rate difference
        external_fx_break = CanonicalTrade(
            trade_id="FX001_CONF",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="FX_FWD",
            currency1="USD",
            currency2="EUR",
            notional1=Decimal("1000000"),
            notional2=Decimal("920000"),
            forward_rate=Decimal("0.9205"),  # 0.5% higher rate
            value_date=date(2024, 1, 17)
        )
        
        internal_trades = [self.internal_fx]
        external_trades = [external_fx_break]
        
        result = self.engine.reconcile_trades(internal_trades, external_trades)
        
        assert result.matched_count == 0
        assert result.exception_count == 1
        
        exception = result.exceptions[0]
        assert exception.exception_type == ExceptionType.PRICE_BREAK
        assert exception.trade_id == "FX001"
        assert "bp" in exception.difference_summary
    
    def test_missing_external_confirmation(self):
        """Test internal trade without external confirmation."""
        internal_trades = [self.internal_irs]
        external_trades = []  # No external confirmations
        
        result = self.engine.reconcile_trades(internal_trades, external_trades)
        
        assert result.matched_count == 0
        assert result.exception_count == 1
        
        exception = result.exceptions[0]
        assert exception.exception_type == ExceptionType.MISSING_EXTERNAL
        assert exception.trade_id == "IRS001"
        assert "Missing external confirmation" in exception.difference_summary
    
    def test_unexpected_external_confirmation(self):
        """Test external confirmation without internal trade."""
        internal_trades = []  # No internal trades
        external_trades = [self.external_irs_match]
        
        result = self.engine.reconcile_trades(internal_trades, external_trades)
        
        assert result.matched_count == 0
        assert result.exception_count == 1
        
        exception = result.exceptions[0]
        assert exception.exception_type == ExceptionType.MISSING_INTERNAL
        assert exception.trade_id == "IRS001_CONF"
        assert "Missing internal trade" in exception.difference_summary
    
    def test_notional_break_exceeds_tolerance(self):
        """Test notional difference exceeding tolerance."""
        # Create external trade with notional difference
        external_irs_notional_break = CanonicalTrade(
            trade_id="IRS001_CONF",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="IRS",
            notional=Decimal("10000100"),  # 100 units higher (exceeds tolerance of 1)
            currency="USD",
            effective_date=date(2024, 1, 17),
            maturity_date=date(2029, 1, 17),
            fixed_rate=Decimal("0.035"),
            floating_index="USD-LIBOR-BBA",
            floating_spread=Decimal("0.0025"),
            pay_receive="PAY",
            day_count="ACT/360"
        )
        
        internal_trades = [self.internal_irs]
        external_trades = [external_irs_notional_break]
        
        result = self.engine.reconcile_trades(internal_trades, external_trades)
        
        assert result.matched_count == 0
        assert result.exception_count == 1
        
        exception = result.exceptions[0]
        assert exception.exception_type == ExceptionType.QTY_BREAK
        assert "USD 100" in exception.difference_summary
    
    def test_date_break_exceeds_tolerance(self):
        """Test date difference exceeding tolerance."""
        # Create external trade with different effective date
        external_irs_date_break = CanonicalTrade(
            trade_id="IRS001_CONF",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="IRS",
            notional=Decimal("10000000"),
            currency="USD",
            effective_date=date(2024, 1, 18),  # 1 day later (exceeds tolerance of 0)
            maturity_date=date(2029, 1, 17),
            fixed_rate=Decimal("0.035"),
            floating_index="USD-LIBOR-BBA",
            floating_spread=Decimal("0.0025"),
            pay_receive="PAY",
            day_count="ACT/360"
        )
        
        internal_trades = [self.internal_irs]
        external_trades = [external_irs_date_break]
        
        result = self.engine.reconcile_trades(internal_trades, external_trades)
        
        assert result.matched_count == 0
        assert result.exception_count == 1
        
        exception = result.exceptions[0]
        assert exception.exception_type == ExceptionType.OTHER
        assert "1 days" in exception.difference_summary
    
    def test_multiple_trades_mixed_results(self):
        """Test reconciliation with multiple trades and mixed results."""
        # Create additional trades
        internal_irs2 = CanonicalTrade(
            trade_id="IRS002",
            trade_date=date(2024, 1, 16),
            counterparty="BANK2",
            product_type="IRS",
            notional=Decimal("5000000"),
            currency="EUR",
            effective_date=date(2024, 1, 18),
            maturity_date=date(2027, 1, 18),
            fixed_rate=Decimal("0.025"),
            floating_index="EUR-EURIBOR-Reuters",
            pay_receive="RECEIVE",
            day_count="ACT/365"
        )
        
        external_irs2_match = CanonicalTrade(
            trade_id="IRS002_CONF",
            trade_date=date(2024, 1, 16),
            counterparty="BANK2",
            product_type="IRS",
            notional=Decimal("5000000"),
            currency="EUR",
            effective_date=date(2024, 1, 18),
            maturity_date=date(2027, 1, 18),
            fixed_rate=Decimal("0.025"),
            floating_index="EUR-EURIBOR-Reuters",
            pay_receive="RECEIVE",
            day_count="ACT/365"
        )
        
        # IRS001 has rate break, IRS002 matches perfectly, FX001 missing external
        internal_trades = [self.internal_irs, internal_irs2, self.internal_fx]
        external_trades = [self.external_irs_match, external_irs2_match]  # Missing FX confirmation
        
        # Modify IRS001 external to have rate break
        self.external_irs_match.fixed_rate = Decimal("0.0351")  # 10 bp difference
        
        result = self.engine.reconcile_trades(internal_trades, external_trades)
        
        assert result.total_internal == 3
        assert result.total_external == 2
        assert result.matched_count == 1  # Only IRS002 matches
        assert result.exception_count == 2  # IRS001 rate break, FX001 missing external
        
        # Check exception types
        exception_types = [exc.exception_type for exc in result.exceptions]
        assert ExceptionType.PRICE_BREAK in exception_types
        assert ExceptionType.MISSING_EXTERNAL in exception_types


class TestOTCMatchKey:
    """Test OTC match key generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = OTCReconEngine()
    
    def test_irs_match_key_generation(self):
        """Test IRS match key generation."""
        irs_trade = CanonicalTrade(
            trade_id="IRS001",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="IRS",
            notional=Decimal("10000000"),
            currency="USD",
            effective_date=date(2024, 1, 17),
            maturity_date=date(2029, 1, 17),
            fixed_rate=Decimal("0.035"),
            pay_receive="PAY"
        )
        
        key = self.engine._create_match_key(irs_trade)
        
        assert key.counterparty == "BANK1"
        assert key.trade_date == date(2024, 1, 15)
        assert key.effective_date == date(2024, 1, 17)
        assert key.maturity_date == date(2029, 1, 17)
        assert key.pay_receive == "PAY"
        assert key.notional == Decimal("10000000")
        assert key.currency == "USD"
        assert key.fixed_rate == Decimal("0.035")
        assert key.forward_rate is None
        assert key.currency_pair is None
    
    def test_fx_match_key_generation(self):
        """Test FX Forward match key generation."""
        fx_trade = CanonicalTrade(
            trade_id="FX001",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="FX_FWD",
            currency1="USD",
            currency2="EUR",
            notional1=Decimal("1000000"),
            forward_rate=Decimal("0.92"),
            value_date=date(2024, 1, 17)
        )
        
        key = self.engine._create_match_key(fx_trade)
        
        assert key.counterparty == "BANK1"
        assert key.trade_date == date(2024, 1, 15)
        assert key.effective_date == date(2024, 1, 17)  # Uses value_date
        assert key.maturity_date == date(2024, 1, 17)
        assert key.pay_receive is None
        assert key.notional == Decimal("1000000")
        assert key.currency == "USD"
        assert key.forward_rate == Decimal("0.92")
        assert key.currency_pair == "EUR/USD"  # Alphabetical order
        assert key.fixed_rate is None
    
    def test_unsupported_product_type(self):
        """Test unsupported product type raises error."""
        unsupported_trade = CanonicalTrade(
            trade_id="UNSUPPORTED001",
            trade_date=date(2024, 1, 15),
            counterparty="BANK1",
            product_type="CREDIT_DEFAULT_SWAP"  # Not supported
        )
        
        with pytest.raises(ValueError, match="Unsupported product type"):
            self.engine._create_match_key(unsupported_trade)


class TestEconomicDifference:
    """Test economic difference analysis."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = OTCReconEngine()
    
    def test_irs_economic_comparison(self):
        """Test IRS economic term comparison."""
        internal_irs = CanonicalTrade(
            trade_id="IRS001",
            product_type="IRS",
            fixed_rate=Decimal("0.035"),
            notional=Decimal("10000000"),
            currency="USD",
            trade_date=date(2024, 1, 15),
            effective_date=date(2024, 1, 17),
            maturity_date=date(2029, 1, 17),
            pay_receive="PAY",
            floating_index="USD-LIBOR-BBA"
        )
        
        external_irs = CanonicalTrade(
            trade_id="IRS001_CONF",
            product_type="IRS",
            fixed_rate=Decimal("0.0351"),  # 10 bp higher
            notional=Decimal("10000050"),  # 50 units higher
            currency="USD",
            trade_date=date(2024, 1, 15),
            effective_date=date(2024, 1, 18),  # 1 day later
            maturity_date=date(2029, 1, 17),
            pay_receive="PAY",
            floating_index="USD-LIBOR-BBA"
        )
        
        differences = self.engine._compare_economic_terms(internal_irs, external_irs)
        
        # Should find differences in rate, notional, and effective date
        diff_fields = [diff.field_name for diff in differences]
        assert "fixed_rate" in diff_fields
        assert "notional" in diff_fields
        assert "effective_date" in diff_fields
        
        # Check rate difference calculation
        rate_diff = next(diff for diff in differences if diff.field_name == "fixed_rate")
        assert rate_diff.difference == Decimal("10")  # 10 bp
        assert not rate_diff.is_within_tolerance  # Exceeds 0.5 bp tolerance
        assert "10.0 bp" in rate_diff.formatted_difference
    
    def test_fx_economic_comparison(self):
        """Test FX Forward economic term comparison."""
        internal_fx = CanonicalTrade(
            trade_id="FX001",
            product_type="FX_FWD",
            currency1="USD",
            currency2="EUR",
            notional1=Decimal("1000000"),
            forward_rate=Decimal("0.92"),
            trade_date=date(2024, 1, 15),
            value_date=date(2024, 1, 17)
        )
        
        external_fx = CanonicalTrade(
            trade_id="FX001_CONF",
            product_type="FX_FWD",
            currency1="USD",
            currency2="EUR",
            notional1=Decimal("1000100"),  # 100 units higher
            forward_rate=Decimal("0.9205"),  # ~0.5% higher
            trade_date=date(2024, 1, 15),
            value_date=date(2024, 1, 17)
        )
        
        differences = self.engine._compare_economic_terms(internal_fx, external_fx)
        
        # Should find differences in rate and notional
        diff_fields = [diff.field_name for diff in differences]
        assert "forward_rate" in diff_fields
        assert "notional1" in diff_fields
        
        # Check rate difference calculation
        rate_diff = next(diff for diff in differences if diff.field_name == "forward_rate")
        assert not rate_diff.is_within_tolerance  # Should exceed tolerance
        assert "bp" in rate_diff.formatted_difference


class TestOTCToleranceConfig:
    """Test OTC tolerance configuration."""
    
    def test_default_tolerance_config(self):
        """Test default tolerance configuration."""
        config = OTCToleranceConfig()
        
        assert config.rate_tolerance_bp == Decimal('0.5')
        assert config.date_tolerance_days == 0
        assert config.notional_tolerance == Decimal('1')
        assert config.irs_rate_tolerance_bp is None
        assert config.fx_rate_tolerance_bp is None
    
    def test_custom_tolerance_config(self):
        """Test custom tolerance configuration."""
        config = OTCToleranceConfig(
            rate_tolerance_bp=Decimal('1.0'),
            date_tolerance_days=1,
            notional_tolerance=Decimal('10'),
            irs_rate_tolerance_bp=Decimal('0.25'),
            fx_rate_tolerance_bp=Decimal('2.0')
        )
        
        assert config.rate_tolerance_bp == Decimal('1.0')
        assert config.date_tolerance_days == 1
        assert config.notional_tolerance == Decimal('10')
        assert config.irs_rate_tolerance_bp == Decimal('0.25')
        assert config.fx_rate_tolerance_bp == Decimal('2.0')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
