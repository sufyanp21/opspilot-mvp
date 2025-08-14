"""Tests for SPAN margin delta analysis and narratives."""

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import Mock, patch

from app.intelligence.margin.span_parser import SPANParser, MarginComponents
from app.intelligence.margin.delta_explainer import (
    DeltaExplainer, 
    MarginDelta, 
    DeltaComponent,
    ChangeType
)
from app.publication.reports.margin_delta_report import MarginDeltaReport


class TestSPANParser:
    """Test SPAN file parsing with margin components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = SPANParser()
    
    def test_parse_span_components(self):
        """Test parsing SPAN file into margin components."""
        # Create test CSV data
        test_data = """account,product,series,scan_risk,inter_spread_charge,total_margin,net_position
ACC001,ES,ESZ5,125000,5000,132500,10
ACC001,NQ,NQZ5,87500,3750,93125,5
ACC002,ES,ESZ5,250000,10000,265000,20"""
        
        # Mock CSV reading
        with patch('pandas.read_csv') as mock_read_csv:
            import pandas as pd
            mock_read_csv.return_value = pd.read_csv(pd.io.common.StringIO(test_data))
            
            components = self.parser.parse_span_file("test.csv", date(2024, 1, 15))
        
        assert len(components) == 3
        
        # Check first component
        es_component = components[0]
        assert es_component.account == "ACC001"
        assert es_component.product == "ES"
        assert es_component.series == "ESZ5"
        assert es_component.scan_risk == Decimal("125000")
        assert es_component.total_margin == Decimal("132500")
        assert es_component.net_position == 10
    
    def test_normalize_column_names(self):
        """Test column name normalization."""
        import pandas as pd
        
        # Test various column name formats
        test_df = pd.DataFrame({
            "Account": ["ACC001"],
            "Symbol": ["ES"],
            "Scan Risk": [125000],
            "Total": [132500]
        })
        
        normalized = self.parser._normalize_columns(test_df)
        
        assert "account" in normalized.columns
        assert "product" in normalized.columns
        assert "scan_risk" in normalized.columns
        assert "total_margin" in normalized.columns


class TestDeltaExplainer:
    """Test margin delta analysis and narrative generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.explainer = DeltaExplainer()
        
        # Create test margin components
        self.prior_es = MarginComponents(
            account="ACC001",
            product="ES",
            series="ESZ5",
            as_of_date=date(2024, 1, 14),
            scan_risk=Decimal("125000"),
            inter_spread_charge=Decimal("5000"),
            short_opt_minimum=Decimal("0"),
            long_opt_credit=Decimal("0"),
            net_premium=Decimal("0"),
            add_on_margin=Decimal("2500"),
            total_margin=Decimal("132500"),
            net_position=10
        )
        
        self.current_es = MarginComponents(
            account="ACC001",
            product="ES",
            series="ESZ5",
            as_of_date=date(2024, 1, 15),
            scan_risk=Decimal("150000"),  # Increased by 25000
            inter_spread_charge=Decimal("5000"),
            short_opt_minimum=Decimal("0"),
            long_opt_credit=Decimal("0"),
            net_premium=Decimal("0"),
            add_on_margin=Decimal("2500"),
            total_margin=Decimal("157500"),  # Total increase of 25000
            net_position=10  # Same position
        )
    
    def test_scan_risk_increase_narrative(self):
        """Test narrative generation for scan risk increase."""
        prior_components = {("ACC001", "ES"): self.prior_es}
        current_components = {("ACC001", "ES"): self.current_es}
        
        deltas = self.explainer.analyze_deltas(prior_components, current_components)
        
        assert len(deltas) == 1
        delta = deltas[0]
        
        assert delta.total_delta == Decimal("25000")
        assert delta.primary_driver == ChangeType.SCAN_RISK
        assert "scan risk" in delta.narrative.lower()
        assert "25,000" in delta.narrative or "25000" in delta.narrative
        assert "ES" in delta.narrative
    
    def test_new_product_narrative(self):
        """Test narrative for new product positions."""
        prior_components = {}  # No prior position
        current_components = {("ACC001", "ES"): self.current_es}
        
        deltas = self.explainer.analyze_deltas(prior_components, current_components)
        
        assert len(deltas) == 1
        delta = deltas[0]
        
        assert delta.primary_driver == ChangeType.NEW_PRODUCT
        assert delta.total_delta == self.current_es.total_margin
        assert "new" in delta.narrative.lower() or "established" in delta.narrative.lower()
        assert "ES" in delta.narrative


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
