"""Unit tests for FpML parser."""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch, mock_open
import tempfile
import os

from app.ingestion.parsers.fpml_parser import (
    FpMLParser, 
    CanonicalTrade, 
    FpMLValidationError,
    CurrencyNormalizer,
    DayCountNormalizer
)


class TestFpMLParser:
    """Test FpML parsing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = FpMLParser()
    
    def test_parse_irs_fpml(self):
        """Test parsing of IRS FpML document."""
        fpml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <fpml:dataDocument xmlns:fpml="http://www.fpml.org/FpML-5/confirmation" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <fpml:trade>
                <fpml:tradeHeader>
                    <fpml:partyTradeIdentifier>
                        <fpml:partyReference href="BANK1"/>
                        <fpml:tradeId>IRS001</fpml:tradeId>
                    </fpml:partyTradeIdentifier>
                    <fpml:tradeDate>2024-01-15</fpml:tradeDate>
                </fpml:tradeHeader>
                <fpml:swap>
                    <fpml:swapStream>
                        <fpml:payerPartyReference href="BANK1"/>
                        <fpml:receiverPartyReference href="CLIENT1"/>
                        <fpml:calculationPeriodDates>
                            <fpml:effectiveDate>
                                <fpml:unadjustedDate>2024-01-17</fpml:unadjustedDate>
                            </fpml:effectiveDate>
                            <fpml:terminationDate>
                                <fpml:unadjustedDate>2029-01-17</fpml:unadjustedDate>
                            </fpml:terminationDate>
                        </fpml:calculationPeriodDates>
                        <fpml:calculationPeriodAmount>
                            <fpml:calculation>
                                <fpml:notionalSchedule>
                                    <fpml:notionalStepSchedule>
                                        <fpml:initialValue>10000000</fpml:initialValue>
                                        <fpml:currency>USD</fpml:currency>
                                    </fpml:notionalStepSchedule>
                                </fpml:notionalSchedule>
                                <fpml:fixedRateSchedule>
                                    <fpml:initialValue>0.035</fpml:initialValue>
                                </fpml:fixedRateSchedule>
                                <fpml:dayCountFraction>ACT/360</fpml:dayCountFraction>
                            </fpml:calculation>
                        </fpml:calculationPeriodAmount>
                    </fpml:swapStream>
                    <fpml:swapStream>
                        <fpml:payerPartyReference href="CLIENT1"/>
                        <fpml:receiverPartyReference href="BANK1"/>
                        <fpml:calculationPeriodDates>
                            <fpml:effectiveDate>
                                <fpml:unadjustedDate>2024-01-17</fpml:unadjustedDate>
                            </fpml:effectiveDate>
                            <fpml:terminationDate>
                                <fpml:unadjustedDate>2029-01-17</fpml:unadjustedDate>
                            </fpml:terminationDate>
                        </fpml:calculationPeriodDates>
                        <fpml:calculationPeriodAmount>
                            <fpml:calculation>
                                <fpml:notionalSchedule>
                                    <fpml:notionalStepSchedule>
                                        <fpml:initialValue>10000000</fpml:initialValue>
                                        <fpml:currency>USD</fpml:currency>
                                    </fpml:notionalStepSchedule>
                                </fpml:notionalSchedule>
                                <fpml:floatingRateCalculation>
                                    <fpml:floatingRateIndex>USD-LIBOR-BBA</fpml:floatingRateIndex>
                                    <fpml:spread>0.0025</fpml:spread>
                                </fpml:floatingRateCalculation>
                                <fpml:dayCountFraction>ACT/360</fpml:dayCountFraction>
                            </fpml:calculation>
                        </fpml:calculationPeriodAmount>
                    </fpml:swapStream>
                </fpml:swap>
            </fpml:trade>
        </fpml:dataDocument>"""
        
        trades = self.parser.parse_xml_content(fpml_content, "test_irs.xml")
        
        assert len(trades) == 1
        trade = trades[0]
        
        assert trade.trade_id == "IRS001"
        assert trade.trade_date == date(2024, 1, 15)
        assert trade.counterparty == "BANK1"
        assert trade.product_type == "IRS"
        assert trade.notional == Decimal("10000000")
        assert trade.currency == "USD"
        assert trade.effective_date == date(2024, 1, 17)
        assert trade.maturity_date == date(2029, 1, 17)
        assert trade.fixed_rate == Decimal("0.035")
        assert trade.floating_index == "USD-LIBOR-BBA"
        assert trade.floating_spread == Decimal("0.0025")
        assert trade.pay_receive == "PAY"  # BANK1 pays fixed
        assert trade.day_count == "ACT/360"
    
    def test_parse_fx_forward_fpml(self):
        """Test parsing of FX Forward FpML document."""
        fpml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <fpml:dataDocument xmlns:fpml="http://www.fpml.org/FpML-5/confirmation" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <fpml:trade>
                <fpml:tradeHeader>
                    <fpml:partyTradeIdentifier>
                        <fpml:partyReference href="BANK1"/>
                        <fpml:tradeId>FX001</fpml:tradeId>
                    </fpml:partyTradeIdentifier>
                    <fpml:tradeDate>2024-01-15</fpml:tradeDate>
                </fpml:tradeHeader>
                <fpml:fxSingleLeg>
                    <fpml:valueDate>2024-01-17</fpml:valueDate>
                    <fpml:exchangedCurrency1>
                        <fpml:paymentAmount>
                            <fpml:currency>USD</fpml:currency>
                            <fpml:amount>1000000</fpml:amount>
                        </fpml:paymentAmount>
                    </fpml:exchangedCurrency1>
                    <fpml:exchangedCurrency2>
                        <fpml:paymentAmount>
                            <fpml:currency>EUR</fpml:currency>
                            <fpml:amount>920000</fpml:amount>
                        </fpml:paymentAmount>
                    </fpml:exchangedCurrency2>
                </fpml:fxSingleLeg>
            </fpml:trade>
        </fpml:dataDocument>"""
        
        trades = self.parser.parse_xml_content(fpml_content, "test_fx.xml")
        
        assert len(trades) == 1
        trade = trades[0]
        
        assert trade.trade_id == "FX001"
        assert trade.trade_date == date(2024, 1, 15)
        assert trade.counterparty == "BANK1"
        assert trade.product_type == "FX_FWD"
        assert trade.currency1 == "USD"
        assert trade.currency2 == "EUR"
        assert trade.notional1 == Decimal("1000000")
        assert trade.notional2 == Decimal("920000")
        assert trade.value_date == date(2024, 1, 17)
        assert trade.forward_rate == Decimal("0.92")  # 920000 / 1000000
    
    def test_parse_invalid_xml(self):
        """Test parsing of invalid XML raises appropriate error."""
        invalid_xml = "<invalid>xml without closing tag"
        
        with pytest.raises(ValueError, match="Invalid FpML XML"):
            self.parser.parse_xml_content(invalid_xml)
    
    def test_parse_empty_fpml(self):
        """Test parsing FpML with no trades raises error."""
        empty_fpml = """<?xml version="1.0" encoding="UTF-8"?>
        <fpml:dataDocument xmlns:fpml="http://www.fpml.org/FpML-5/confirmation">
            <!-- No trades -->
        </fpml:dataDocument>"""
        
        with pytest.raises(ValueError, match="No trade elements found"):
            self.parser.parse_xml_content(empty_fpml)
    
    def test_parse_zip_file(self):
        """Test parsing ZIP file containing multiple FpML documents."""
        # Create temporary ZIP file with mock content
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            import zipfile
            
            with zipfile.ZipFile(temp_zip.name, 'w') as zf:
                # Add mock FpML content
                zf.writestr('trade1.xml', """<?xml version="1.0" encoding="UTF-8"?>
                    <fpml:dataDocument xmlns:fpml="http://www.fpml.org/FpML-5/confirmation">
                        <fpml:trade>
                            <fpml:tradeHeader>
                                <fpml:partyTradeIdentifier>
                                    <fpml:tradeId>ZIP001</fpml:tradeId>
                                </fpml:partyTradeIdentifier>
                                <fpml:tradeDate>2024-01-15</fpml:tradeDate>
                            </fpml:tradeHeader>
                            <fpml:fxSingleLeg>
                                <fpml:valueDate>2024-01-17</fpml:valueDate>
                                <fpml:exchangedCurrency1>
                                    <fpml:paymentAmount>
                                        <fpml:currency>USD</fpml:currency>
                                        <fpml:amount>500000</fpml:amount>
                                    </fpml:paymentAmount>
                                </fpml:exchangedCurrency1>
                                <fpml:exchangedCurrency2>
                                    <fpml:paymentAmount>
                                        <fpml:currency>GBP</fpml:currency>
                                        <fpml:amount>400000</fpml:amount>
                                    </fpml:paymentAmount>
                                </fpml:exchangedCurrency2>
                            </fpml:fxSingleLeg>
                        </fpml:trade>
                    </fpml:dataDocument>""")
            
            try:
                trades = self.parser.parse_file(temp_zip.name)
                assert len(trades) == 1
                assert trades[0].trade_id == "ZIP001"
            finally:
                os.unlink(temp_zip.name)
    
    def test_date_parsing_formats(self):
        """Test various date format parsing."""
        test_cases = [
            ("2024-01-15", date(2024, 1, 15)),
            ("15/01/2024", date(2024, 1, 15)),
            ("01/15/2024", date(2024, 1, 15)),
            ("20240115", date(2024, 1, 15))
        ]
        
        for date_str, expected_date in test_cases:
            result = self.parser._parse_date(date_str)
            assert result == expected_date
    
    def test_invalid_date_parsing(self):
        """Test invalid date format raises error."""
        with pytest.raises(ValueError, match="Unable to parse date"):
            self.parser._parse_date("invalid-date")
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        incomplete_fpml = """<?xml version="1.0" encoding="UTF-8"?>
        <fpml:dataDocument xmlns:fpml="http://www.fpml.org/FpML-5/confirmation">
            <fpml:trade>
                <fpml:tradeHeader>
                    <!-- Missing trade ID -->
                    <fpml:tradeDate>2024-01-15</fpml:tradeDate>
                </fpml:tradeHeader>
                <fpml:fxSingleLeg>
                    <!-- Incomplete FX trade -->
                </fpml:fxSingleLeg>
            </fpml:trade>
        </fpml:dataDocument>"""
        
        # Should handle gracefully and skip invalid trades
        trades = self.parser.parse_xml_content(incomplete_fpml)
        assert len(trades) == 0  # No valid trades parsed


class TestCurrencyNormalizer:
    """Test currency normalization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = CurrencyNormalizer()
    
    def test_normalize_standard_currencies(self):
        """Test normalization of standard currency codes."""
        test_cases = [
            ("usd", "USD"),
            ("USD", "USD"),
            ("eur", "EUR"),
            ("gbp", "GBP"),
            ("  JPY  ", "JPY")
        ]
        
        for input_currency, expected in test_cases:
            result = self.normalizer.normalize(input_currency)
            assert result == expected
    
    def test_normalize_unknown_currency(self):
        """Test handling of unknown currency codes."""
        result = self.normalizer.normalize("XYZ")
        assert result == "XYZ"  # Should return as-is
    
    def test_normalize_empty_currency(self):
        """Test handling of empty currency."""
        result = self.normalizer.normalize("")
        assert result == ""
        
        result = self.normalizer.normalize(None)
        assert result is None


class TestDayCountNormalizer:
    """Test day count convention normalization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = DayCountNormalizer()
    
    def test_normalize_standard_conventions(self):
        """Test normalization of standard day count conventions."""
        test_cases = [
            ("ACTUAL/360", "ACT/360"),
            ("act/360", "ACT/360"),
            ("ACTUAL/ACTUAL", "ACT/ACT"),
            ("30/360", "30/360"),
            ("30E/360", "30E/360")
        ]
        
        for input_daycount, expected in test_cases:
            result = self.normalizer.normalize(input_daycount)
            assert result == expected
    
    def test_normalize_unknown_convention(self):
        """Test handling of unknown day count conventions."""
        result = self.normalizer.normalize("CUSTOM/CONVENTION")
        assert result == "CUSTOM/CONVENTION"  # Should return as-is


class TestFpMLValidationError:
    """Test FpML validation error handling."""
    
    def test_validation_error_with_xpath(self):
        """Test validation error with XPath information."""
        error = FpMLValidationError("Missing required field", "//fpml:tradeId")
        
        assert "Missing required field" in str(error)
        assert "//fpml:tradeId" in str(error)
    
    def test_validation_error_without_xpath(self):
        """Test validation error without XPath information."""
        error = FpMLValidationError("General validation error")
        
        assert "General validation error" in str(error)
        assert "at" not in str(error)


class TestIntegration:
    """Integration tests for FpML parsing workflow."""
    
    def test_end_to_end_irs_parsing(self):
        """Test complete IRS parsing workflow."""
        # This would test the complete flow:
        # 1. Parse FpML file
        # 2. Validate business rules
        # 3. Normalize fields
        # 4. Create canonical trades
        
        parser = FpMLParser()
        
        # Mock complete IRS FpML document
        complete_irs_fpml = """<?xml version="1.0" encoding="UTF-8"?>
        <fpml:dataDocument xmlns:fpml="http://www.fpml.org/FpML-5/confirmation">
            <fpml:trade>
                <fpml:tradeHeader>
                    <fpml:partyTradeIdentifier>
                        <fpml:partyReference href="COUNTERPARTY1"/>
                        <fpml:tradeId>IRS_INTEGRATION_001</fpml:tradeId>
                    </fpml:partyTradeIdentifier>
                    <fpml:tradeDate>2024-01-15</fpml:tradeDate>
                </fpml:tradeHeader>
                <fpml:usi>
                    <fpml:utiIdentifier>1234567890ABCDEF1234567890ABCDEF12345678</fpml:utiIdentifier>
                </fpml:usi>
                <fpml:swap>
                    <fpml:swapStream>
                        <fpml:payerPartyReference href="COUNTERPARTY1"/>
                        <fpml:receiverPartyReference href="BANK1"/>
                        <fpml:calculationPeriodDates>
                            <fpml:effectiveDate>
                                <fpml:unadjustedDate>2024-01-17</fpml:unadjustedDate>
                            </fpml:effectiveDate>
                            <fpml:terminationDate>
                                <fpml:unadjustedDate>2034-01-17</fpml:unadjustedDate>
                            </fpml:terminationDate>
                        </fpml:calculationPeriodDates>
                        <fpml:calculationPeriodAmount>
                            <fpml:calculation>
                                <fpml:notionalSchedule>
                                    <fpml:notionalStepSchedule>
                                        <fpml:initialValue>50000000</fpml:initialValue>
                                        <fpml:currency>USD</fpml:currency>
                                    </fpml:notionalStepSchedule>
                                </fpml:notionalSchedule>
                                <fpml:fixedRateSchedule>
                                    <fpml:initialValue>0.0425</fpml:initialValue>
                                </fpml:fixedRateSchedule>
                                <fpml:dayCountFraction>ACTUAL/360</fpml:dayCountFraction>
                            </fpml:calculation>
                        </fpml:calculationPeriodAmount>
                    </fpml:swapStream>
                    <fpml:swapStream>
                        <fpml:payerPartyReference href="BANK1"/>
                        <fpml:receiverPartyReference href="COUNTERPARTY1"/>
                        <fpml:calculationPeriodDates>
                            <fpml:effectiveDate>
                                <fpml:unadjustedDate>2024-01-17</fpml:unadjustedDate>
                            </fpml:effectiveDate>
                            <fpml:terminationDate>
                                <fpml:unadjustedDate>2034-01-17</fpml:unadjustedDate>
                            </fpml:terminationDate>
                        </fpml:calculationPeriodDates>
                        <fpml:calculationPeriodAmount>
                            <fpml:calculation>
                                <fpml:notionalSchedule>
                                    <fpml:notionalStepSchedule>
                                        <fpml:initialValue>50000000</fpml:initialValue>
                                        <fpml:currency>USD</fpml:currency>
                                    </fpml:notionalStepSchedule>
                                </fpml:notionalSchedule>
                                <fpml:floatingRateCalculation>
                                    <fpml:floatingRateIndex>USD-SOFR-COMPOUND</fpml:floatingRateIndex>
                                    <fpml:spread>0.0050</fpml:spread>
                                </fpml:floatingRateCalculation>
                                <fpml:dayCountFraction>ACTUAL/360</fpml:dayCountFraction>
                            </fpml:calculation>
                        </fpml:calculationPeriodAmount>
                    </fpml:swapStream>
                </fpml:swap>
            </fpml:trade>
        </fpml:dataDocument>"""
        
        trades = parser.parse_xml_content(complete_irs_fpml, "integration_test.xml")
        
        assert len(trades) == 1
        trade = trades[0]
        
        # Verify all fields are properly parsed and normalized
        assert trade.trade_id == "IRS_INTEGRATION_001"
        assert trade.counterparty == "COUNTERPARTY1"
        assert trade.uti == "1234567890ABCDEF1234567890ABCDEF12345678"
        assert trade.notional == Decimal("50000000")
        assert trade.currency == "USD"
        assert trade.fixed_rate == Decimal("0.0425")
        assert trade.floating_index == "USD-SOFR-COMPOUND"
        assert trade.floating_spread == Decimal("0.0050")
        assert trade.day_count == "ACT/360"  # Normalized from ACTUAL/360
        assert trade.pay_receive == "RECEIVE"  # COUNTERPARTY1 pays fixed, so we receive fixed
        assert trade.source_file == "integration_test.xml"
        assert trade.parsed_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
