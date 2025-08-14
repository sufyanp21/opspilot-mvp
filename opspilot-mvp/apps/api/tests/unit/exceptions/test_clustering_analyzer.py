"""Unit tests for exception clustering analyzer."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from app.exceptions.clustering_analyzer import (
    ExceptionClusteringAnalyzer, 
    ClusteringConfig, 
    ClusteringMethod,
    ExceptionCluster
)
from app.models.recon import ReconException, ExceptionStatus


class TestExceptionClusteringAnalyzer:
    """Test cases for exception clustering analyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ExceptionClusteringAnalyzer()
        self.config = ClusteringConfig(
            min_cluster_size=2,
            max_clusters_per_run=10
        )
        self.analyzer.config = self.config
    
    def create_mock_exception(
        self, 
        trade_id: str, 
        symbol: str = "ES_FUT", 
        account: str = "BANK_001",
        difference_summary: str = "Price mismatch: 100.25 vs 100.50"
    ) -> ReconException:
        """Create mock exception for testing."""
        exception = Mock(spec=ReconException)
        exception.trade_id = trade_id
        exception.symbol = symbol
        exception.account = account
        exception.difference_summary = difference_summary
        exception.exception_type = "PRICE_BREAK"
        exception.internal_qty = 1000
        exception.external_qty = 1000
        return exception
    
    def test_analyze_exceptions_empty_list(self):
        """Test clustering with empty exception list."""
        clusters = self.analyzer.analyze_exceptions([])
        assert clusters == []
    
    def test_analyze_exceptions_single_exception(self):
        """Test clustering with single exception (below min cluster size)."""
        exceptions = [self.create_mock_exception("TRADE_001")]
        clusters = self.analyzer.analyze_exceptions(exceptions)
        assert len(clusters) == 0  # Below min cluster size
    
    def test_exact_match_clustering(self):
        """Test exact match clustering for similar exceptions."""
        exceptions = [
            self.create_mock_exception("TRADE_001", "ES_FUT", "BANK_001", "Price mismatch: 100.25 vs 100.50"),
            self.create_mock_exception("TRADE_002", "ES_FUT", "BANK_001", "Price mismatch: 101.25 vs 101.50"),
            self.create_mock_exception("TRADE_003", "NQ_FUT", "BROKER_001", "Quantity mismatch: 100 vs 200")
        ]
        
        clusters = self.analyzer.analyze_exceptions(exceptions)
        
        # Should create one cluster for ES_FUT price mismatches
        assert len(clusters) == 1
        cluster = clusters[0]
        assert cluster.clustering_method == ClusteringMethod.EXACT_MATCH
        assert cluster.exception_count == 2
        assert "ES_FUTURES" in cluster.cluster_key
        assert cluster.probable_cause == "price_mismatch"
    
    def test_fuzzy_hash_clustering(self):
        """Test fuzzy hash clustering for similar patterns."""
        # Create exceptions with similar patterns but different exact keys
        exceptions = [
            self.create_mock_exception("TRADE_001", "ES_MAR24", "BANK_A", "Price difference: 0.25 ticks"),
            self.create_mock_exception("TRADE_002", "ES_JUN24", "BANK_B", "Price difference: 0.50 ticks"),
            self.create_mock_exception("TRADE_003", "NQ_MAR24", "FUND_A", "Quantity variance: 100 contracts"),
            self.create_mock_exception("TRADE_004", "NQ_JUN24", "FUND_B", "Quantity variance: 200 contracts")
        ]
        
        clusters = self.analyzer.analyze_exceptions(exceptions)
        
        # Should create clusters based on similar patterns
        assert len(clusters) >= 1
        
        # Check that clusters have reasonable properties
        for cluster in clusters:
            assert cluster.exception_count >= 2
            assert cluster.cluster_id.startswith("CLU_")
            assert cluster.probable_cause in ["price_mismatch", "quantity_mismatch", "other"]
    
    def test_cluster_severity_determination(self):
        """Test cluster severity level determination."""
        # High-value exceptions should create high severity cluster
        high_value_exceptions = [
            self.create_mock_exception("TRADE_001", "ES_FUT", "BANK_001", "Price mismatch: large notional"),
            self.create_mock_exception("TRADE_002", "ES_FUT", "BANK_001", "Price mismatch: large notional")
        ]
        
        # Mock high internal_qty for severity calculation
        for exc in high_value_exceptions:
            exc.internal_qty = 10000000  # 10M
        
        clusters = self.analyzer.analyze_exceptions(high_value_exceptions)
        
        if clusters:
            cluster = clusters[0]
            assert cluster.severity_level in ["HIGH", "CRITICAL"]
    
    def test_cluster_statistics(self):
        """Test cluster statistics calculation."""
        exceptions = [
            self.create_mock_exception("TRADE_001", "ES_FUT", "BANK_001", "Price mismatch"),
            self.create_mock_exception("TRADE_002", "ES_FUT", "BANK_002", "Price mismatch"),
            self.create_mock_exception("TRADE_003", "NQ_FUT", "BANK_001", "Price mismatch")
        ]
        
        clusters = self.analyzer.analyze_exceptions(exceptions)
        
        if clusters:
            cluster = clusters[0]
            
            # Check statistics are populated
            assert len(cluster.accounts_affected) > 0
            assert len(cluster.products_affected) > 0
            assert len(cluster.exception_types) > 0
            assert cluster.cluster_metadata is not None
            
            # Check metadata contains expected fields
            metadata = cluster.cluster_metadata
            assert "exception_ids" in metadata
            assert "avg_impact" in metadata
            assert "clustering_features" in metadata
    
    def test_normalize_field_name(self):
        """Test field name normalization for clustering."""
        # Test common field name mappings
        assert self.analyzer._normalize_field_name("price") == "price"
        assert self.analyzer._normalize_field_name("rate") == "price"
        assert self.analyzer._normalize_field_name("fixed_rate") == "price"
        assert self.analyzer._normalize_field_name("quantity") == "quantity"
        assert self.analyzer._normalize_field_name("qty") == "quantity"
        assert self.analyzer._normalize_field_name("notional") == "quantity"
        assert self.analyzer._normalize_field_name("trade_date") == "date"
        assert self.analyzer._normalize_field_name("unknown_field") == "unknown_field"
    
    def test_normalize_product_symbol(self):
        """Test product symbol normalization for clustering."""
        assert self.analyzer._normalize_product_symbol("ES_MAR24_FUT") == "ES_FUTURES"
        assert self.analyzer._normalize_product_symbol("NQ_JUN24_FUT") == "NQ_FUTURES"
        assert self.analyzer._normalize_product_symbol("IRS_5Y_USD") == "IRS"
        assert self.analyzer._normalize_product_symbol("FX_FWD_EURUSD") == "FX_FORWARD"
        assert self.analyzer._normalize_product_symbol("CUSTOM_PRODUCT_LONG_NAME") == "CUSTOM_PRO"  # Truncated
    
    def test_extract_cause_code(self):
        """Test cause code extraction from exception summaries."""
        price_exception = self.create_mock_exception("T1", difference_summary="Price mismatch: 100 vs 101")
        assert self.analyzer._extract_cause_code(price_exception) == "price_mismatch"
        
        qty_exception = self.create_mock_exception("T2", difference_summary="Quantity difference: 100 vs 200")
        assert self.analyzer._extract_cause_code(qty_exception) == "quantity_mismatch"
        
        date_exception = self.create_mock_exception("T3", difference_summary="Trade date mismatch")
        assert self.analyzer._extract_cause_code(date_exception) == "date_mismatch"
        
        missing_exception = self.create_mock_exception("T4", difference_summary="Missing confirmation")
        assert self.analyzer._extract_cause_code(missing_exception) == "missing_trade"
        
        timeout_exception = self.create_mock_exception("T5", difference_summary="System timeout error")
        assert self.analyzer._extract_cause_code(timeout_exception) == "system_timeout"
        
        unknown_exception = self.create_mock_exception("T6", difference_summary="Unknown error occurred")
        assert self.analyzer._extract_cause_code(unknown_exception) == "other"
    
    def test_clustering_config_limits(self):
        """Test clustering configuration limits."""
        # Test max clusters limit
        config = ClusteringConfig(
            min_cluster_size=1,  # Lower threshold for testing
            max_clusters_per_run=2
        )
        self.analyzer.config = config
        
        # Create many different exception types
        exceptions = []
        for i in range(10):
            exceptions.extend([
                self.create_mock_exception(f"TRADE_{i}_1", f"PRODUCT_{i}", f"ACCOUNT_{i}", f"Error type {i}"),
                self.create_mock_exception(f"TRADE_{i}_2", f"PRODUCT_{i}", f"ACCOUNT_{i}", f"Error type {i}")
            ])
        
        clusters = self.analyzer.analyze_exceptions(exceptions)
        
        # Should be limited by max_clusters_per_run
        assert len(clusters) <= config.max_clusters_per_run
    
    def test_cluster_id_generation(self):
        """Test cluster ID generation uniqueness."""
        cluster_key_1 = "type:PRICE_BREAK|product:ES_FUTURES|cause:price_mismatch"
        cluster_key_2 = "type:QTY_BREAK|product:NQ_FUTURES|cause:quantity_mismatch"
        
        id_1 = self.analyzer._generate_cluster_id(cluster_key_1, ClusteringMethod.EXACT_MATCH)
        id_2 = self.analyzer._generate_cluster_id(cluster_key_2, ClusteringMethod.EXACT_MATCH)
        
        # IDs should be unique
        assert id_1 != id_2
        
        # IDs should have expected format
        assert id_1.startswith("CLU_EXAC_")
        assert id_2.startswith("CLU_EXAC_")
        
        # Same key should generate same ID
        id_1_repeat = self.analyzer._generate_cluster_id(cluster_key_1, ClusteringMethod.EXACT_MATCH)
        assert id_1 == id_1_repeat
    
    def test_exception_severity_scoring(self):
        """Test exception severity scoring logic."""
        # Low value exception
        low_exception = self.create_mock_exception("T1")
        low_exception.internal_qty = 1000
        low_score = self.analyzer._get_exception_severity_score(low_exception)
        
        # High value exception
        high_exception = self.create_mock_exception("T2")
        high_exception.internal_qty = 10000000  # 10M
        high_score = self.analyzer._get_exception_severity_score(high_exception)
        
        # High value should have higher severity score
        assert high_score > low_score
        
        # Scores should be in valid range
        assert 1 <= low_score <= 10
        assert 1 <= high_score <= 10
    
    def test_fuzzy_hash_similarity(self):
        """Test fuzzy hash generation for similar exceptions."""
        # Similar exceptions should generate same or similar hashes
        similar_exc_1 = self.create_mock_exception(
            "T1", "ES_MAR24", "BANK_A", "Price difference of 0.25 ticks detected"
        )
        similar_exc_2 = self.create_mock_exception(
            "T2", "ES_JUN24", "BANK_B", "Price difference of 0.50 ticks detected"
        )
        
        hash_1 = self.analyzer._create_fuzzy_hash(similar_exc_1)
        hash_2 = self.analyzer._create_fuzzy_hash(similar_exc_2)
        
        # Hashes should be strings
        assert isinstance(hash_1, str)
        assert isinstance(hash_2, str)
        
        # For very similar patterns, hashes might be the same
        # (This depends on the fuzzy hashing implementation)
        assert len(hash_1) == len(hash_2)  # Same hash length
    
    def test_cluster_representative_selection(self):
        """Test selection of representative exception for cluster."""
        # Create exceptions with different severity levels
        low_exception = self.create_mock_exception("T1", difference_summary="Minor price difference")
        low_exception.internal_qty = 1000
        
        high_exception = self.create_mock_exception("T2", difference_summary="Major price difference")
        high_exception.internal_qty = 10000000
        
        exceptions = [low_exception, high_exception]
        clusters = self.analyzer.analyze_exceptions(exceptions)
        
        if clusters:
            cluster = clusters[0]
            # Representative should be the higher severity exception
            assert cluster.representative_exception.trade_id == "T2"
    
    @pytest.mark.parametrize("enable_exact,enable_fuzzy,expected_methods", [
        (True, True, [ClusteringMethod.EXACT_MATCH, ClusteringMethod.FUZZY_HASH]),
        (True, False, [ClusteringMethod.EXACT_MATCH]),
        (False, True, [ClusteringMethod.FUZZY_HASH]),
        (False, False, [])
    ])
    def test_clustering_method_configuration(self, enable_exact, enable_fuzzy, expected_methods):
        """Test clustering method configuration options."""
        config = ClusteringConfig(
            enable_exact_matching=enable_exact,
            enable_fuzzy_matching=enable_fuzzy,
            min_cluster_size=2
        )
        self.analyzer.config = config
        
        # Create test exceptions
        exceptions = [
            self.create_mock_exception("T1", "ES_FUT", "BANK_001", "Price mismatch"),
            self.create_mock_exception("T2", "ES_FUT", "BANK_001", "Price mismatch"),
            self.create_mock_exception("T3", "NQ_FUT", "BANK_002", "Quantity mismatch"),
            self.create_mock_exception("T4", "NQ_FUT", "BANK_002", "Quantity mismatch")
        ]
        
        clusters = self.analyzer.analyze_exceptions(exceptions)
        
        if expected_methods:
            # Should create clusters using enabled methods
            assert len(clusters) > 0
            for cluster in clusters:
                assert cluster.clustering_method in expected_methods
        else:
            # No clustering methods enabled, should return empty
            assert len(clusters) == 0
