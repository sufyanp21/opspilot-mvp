"""Exception clustering analyzer for grouping similar breaks."""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib
import logging
from collections import defaultdict
from enum import Enum

from app.models.recon import ReconException, ExceptionStatus

logger = logging.getLogger(__name__)


class ClusteringMethod(Enum):
    """Methods for clustering exceptions."""
    EXACT_MATCH = "exact_match"
    FUZZY_HASH = "fuzzy_hash"
    SEMANTIC = "semantic"


@dataclass
class ExceptionCluster:
    """Represents a cluster of similar exceptions."""
    cluster_id: str
    cluster_key: str
    clustering_method: ClusteringMethod
    exception_count: int
    probable_cause: str
    severity_level: str
    created_at: datetime
    updated_at: datetime
    
    # Representative exception for the cluster
    representative_exception: ReconException
    
    # Cluster statistics
    accounts_affected: Set[str]
    products_affected: Set[str]
    exception_types: Set[str]
    
    # Metadata
    cluster_metadata: Dict[str, Any]


@dataclass
class ClusteringConfig:
    """Configuration for exception clustering."""
    enable_exact_matching: bool = True
    enable_fuzzy_matching: bool = True
    fuzzy_similarity_threshold: float = 0.8
    min_cluster_size: int = 2
    max_clusters_per_run: int = 100
    
    # Clustering weights
    recon_type_weight: float = 0.3
    field_weight: float = 0.25
    product_weight: float = 0.2
    counterparty_weight: float = 0.15
    cause_code_weight: float = 0.1


class ExceptionClusteringAnalyzer:
    """Analyzes and clusters similar reconciliation exceptions."""
    
    def __init__(self, config: Optional[ClusteringConfig] = None):
        self.config = config or ClusteringConfig()
        self.clusters: Dict[str, ExceptionCluster] = {}
    
    def analyze_exceptions(self, exceptions: List[ReconException]) -> List[ExceptionCluster]:
        """
        Analyze exceptions and group them into clusters.
        
        Args:
            exceptions: List of reconciliation exceptions to cluster
            
        Returns:
            List of exception clusters
        """
        try:
            logger.info(f"Analyzing {len(exceptions)} exceptions for clustering")
            
            # Clear previous clusters
            self.clusters.clear()
            
            # Group exceptions by clustering methods
            if self.config.enable_exact_matching:
                self._cluster_by_exact_match(exceptions)
            
            if self.config.enable_fuzzy_matching:
                self._cluster_by_fuzzy_hash(exceptions)
            
            # Filter clusters by minimum size
            filtered_clusters = [
                cluster for cluster in self.clusters.values()
                if cluster.exception_count >= self.config.min_cluster_size
            ]
            
            # Sort by severity and size
            filtered_clusters.sort(
                key=lambda c: (self._get_severity_priority(c.severity_level), -c.exception_count)
            )
            
            # Limit number of clusters
            if len(filtered_clusters) > self.config.max_clusters_per_run:
                filtered_clusters = filtered_clusters[:self.config.max_clusters_per_run]
            
            logger.info(f"Created {len(filtered_clusters)} exception clusters")
            return filtered_clusters
            
        except Exception as e:
            logger.error(f"Error in exception clustering analysis: {e}")
            raise
    
    def _cluster_by_exact_match(self, exceptions: List[ReconException]):
        """Cluster exceptions using exact key matching."""
        exact_groups = defaultdict(list)
        
        for exception in exceptions:
            cluster_key = self._create_exact_cluster_key(exception)
            exact_groups[cluster_key].append(exception)
        
        # Create clusters for groups with multiple exceptions
        for cluster_key, group_exceptions in exact_groups.items():
            if len(group_exceptions) >= self.config.min_cluster_size:
                cluster_id = self._generate_cluster_id(cluster_key, ClusteringMethod.EXACT_MATCH)
                
                if cluster_id not in self.clusters:
                    cluster = self._create_cluster(
                        cluster_id, cluster_key, ClusteringMethod.EXACT_MATCH, group_exceptions
                    )
                    self.clusters[cluster_id] = cluster
    
    def _cluster_by_fuzzy_hash(self, exceptions: List[ReconException]):
        """Cluster exceptions using fuzzy hashing for similar patterns."""
        # Get unclustered exceptions
        unclustered = [
            exc for exc in exceptions
            if not self._is_exception_clustered(exc)
        ]
        
        if not unclustered:
            return
        
        # Create fuzzy hashes for unclustered exceptions
        fuzzy_groups = defaultdict(list)
        
        for exception in unclustered:
            fuzzy_hash = self._create_fuzzy_hash(exception)
            fuzzy_groups[fuzzy_hash].append(exception)
        
        # Create clusters for similar groups
        for fuzzy_hash, group_exceptions in fuzzy_groups.items():
            if len(group_exceptions) >= self.config.min_cluster_size:
                cluster_key = f"fuzzy_{fuzzy_hash[:8]}"
                cluster_id = self._generate_cluster_id(cluster_key, ClusteringMethod.FUZZY_HASH)
                
                if cluster_id not in self.clusters:
                    cluster = self._create_cluster(
                        cluster_id, cluster_key, ClusteringMethod.FUZZY_HASH, group_exceptions
                    )
                    self.clusters[cluster_id] = cluster
    
    def _create_exact_cluster_key(self, exception: ReconException) -> str:
        """Create exact cluster key for exception."""
        # Use combination of key fields for exact matching
        key_components = [
            exception.exception_type.value if hasattr(exception.exception_type, 'value') else str(exception.exception_type),
            self._normalize_field_name(getattr(exception, 'field_name', 'unknown')),
            self._normalize_product_symbol(exception.symbol),
            self._normalize_counterparty(exception.account),
            self._extract_cause_code(exception)
        ]
        
        # Remove None values and join
        key_components = [str(comp) for comp in key_components if comp is not None]
        return "|".join(key_components)
    
    def _create_fuzzy_hash(self, exception: ReconException) -> str:
        """Create fuzzy hash for exception using MinHash-like approach."""
        # Extract features for fuzzy matching
        features = []
        
        # Exception type features
        if hasattr(exception.exception_type, 'value'):
            features.append(f"type:{exception.exception_type.value}")
        
        # Difference pattern features
        if exception.difference_summary:
            # Extract numeric patterns
            import re
            numbers = re.findall(r'\d+\.?\d*', exception.difference_summary)
            if numbers:
                features.append(f"numeric_pattern:{len(numbers)}")
            
            # Extract common terms
            terms = exception.difference_summary.lower().split()
            common_terms = [term for term in terms if len(term) > 3]
            features.extend([f"term:{term}" for term in common_terms[:5]])
        
        # Product/symbol features
        if exception.symbol:
            product_type = self._extract_product_type(exception.symbol)
            features.append(f"product:{product_type}")
        
        # Account/counterparty features
        if exception.account:
            account_type = self._extract_account_type(exception.account)
            features.append(f"account_type:{account_type}")
        
        # Create hash from features
        feature_string = "|".join(sorted(features))
        return hashlib.md5(feature_string.encode()).hexdigest()
    
    def _create_cluster(
        self, 
        cluster_id: str, 
        cluster_key: str, 
        method: ClusteringMethod, 
        exceptions: List[ReconException]
    ) -> ExceptionCluster:
        """Create exception cluster from grouped exceptions."""
        
        # Select representative exception (first one or most severe)
        representative = exceptions[0]
        for exc in exceptions:
            if self._get_exception_severity_score(exc) > self._get_exception_severity_score(representative):
                representative = exc
        
        # Collect cluster statistics
        accounts_affected = set(exc.account for exc in exceptions if exc.account)
        products_affected = set(exc.symbol for exc in exceptions if exc.symbol)
        exception_types = set(exc.exception_type for exc in exceptions)
        
        # Determine probable cause
        probable_cause = self._determine_probable_cause(exceptions)
        
        # Determine severity level
        severity_level = self._determine_cluster_severity(exceptions)
        
        # Create cluster metadata
        metadata = {
            "exception_ids": [exc.trade_id for exc in exceptions if exc.trade_id],
            "avg_impact": self._calculate_average_impact(exceptions),
            "time_span": self._calculate_time_span(exceptions),
            "geographic_spread": self._analyze_geographic_spread(exceptions),
            "clustering_features": self._extract_clustering_features(exceptions)
        }
        
        now = datetime.utcnow()
        
        return ExceptionCluster(
            cluster_id=cluster_id,
            cluster_key=cluster_key,
            clustering_method=method,
            exception_count=len(exceptions),
            probable_cause=probable_cause,
            severity_level=severity_level,
            created_at=now,
            updated_at=now,
            representative_exception=representative,
            accounts_affected=accounts_affected,
            products_affected=products_affected,
            exception_types=exception_types,
            cluster_metadata=metadata
        )
    
    def _is_exception_clustered(self, exception: ReconException) -> bool:
        """Check if exception is already in a cluster."""
        for cluster in self.clusters.values():
            if exception.trade_id in cluster.cluster_metadata.get("exception_ids", []):
                return True
        return False
    
    def _generate_cluster_id(self, cluster_key: str, method: ClusteringMethod) -> str:
        """Generate unique cluster ID."""
        key_hash = hashlib.sha256(cluster_key.encode()).hexdigest()[:8]
        method_prefix = method.value[:4].upper()
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        return f"CLU_{method_prefix}_{timestamp}_{key_hash}"
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for clustering."""
        if not field_name:
            return "unknown"
        
        # Common field name mappings
        field_mappings = {
            "price": "price",
            "rate": "price",
            "fixed_rate": "price",
            "forward_rate": "price",
            "quantity": "quantity",
            "qty": "quantity",
            "notional": "quantity",
            "amount": "quantity",
            "date": "date",
            "trade_date": "date",
            "effective_date": "date",
            "maturity_date": "date",
            "value_date": "date"
        }
        
        normalized = field_name.lower().strip()
        return field_mappings.get(normalized, normalized)
    
    def _normalize_product_symbol(self, symbol: str) -> str:
        """Normalize product symbol for clustering."""
        if not symbol:
            return "unknown"
        
        # Extract base product from symbol
        symbol = symbol.upper().strip()
        
        # Common product patterns
        if symbol.startswith("ES"):
            return "ES_FUTURES"
        elif symbol.startswith("NQ"):
            return "NQ_FUTURES"
        elif "IRS" in symbol:
            return "IRS"
        elif "FX_FWD" in symbol:
            return "FX_FORWARD"
        
        return symbol[:10]  # Truncate long symbols
    
    def _normalize_counterparty(self, counterparty: str) -> str:
        """Normalize counterparty for clustering."""
        if not counterparty:
            return "unknown"
        
        # Extract counterparty type or group
        counterparty = counterparty.upper().strip()
        
        if counterparty.startswith("BANK"):
            return "BANK"
        elif counterparty.startswith("BROKER"):
            return "BROKER"
        elif counterparty.startswith("CLIENT"):
            return "CLIENT"
        
        return counterparty[:10]  # Truncate long names
    
    def _extract_cause_code(self, exception: ReconException) -> str:
        """Extract probable cause code from exception."""
        if not exception.difference_summary:
            return "unknown"
        
        summary = exception.difference_summary.lower()
        
        # Pattern matching for common causes
        if "price" in summary or "rate" in summary:
            return "price_mismatch"
        elif "quantity" in summary or "notional" in summary:
            return "quantity_mismatch"
        elif "date" in summary:
            return "date_mismatch"
        elif "missing" in summary:
            return "missing_trade"
        elif "unexpected" in summary:
            return "unexpected_trade"
        elif "timeout" in summary:
            return "system_timeout"
        elif "format" in summary or "parsing" in summary:
            return "data_format"
        
        return "other"
    
    def _extract_product_type(self, symbol: str) -> str:
        """Extract product type from symbol."""
        if not symbol:
            return "unknown"
        
        symbol = symbol.upper()
        
        if any(fut in symbol for fut in ["ES", "NQ", "YM", "RTY"]):
            return "equity_futures"
        elif any(bond in symbol for bond in ["ZN", "ZB", "ZF", "ZT"]):
            return "bond_futures"
        elif "IRS" in symbol:
            return "interest_rate_swap"
        elif "FX" in symbol:
            return "fx_forward"
        
        return "other"
    
    def _extract_account_type(self, account: str) -> str:
        """Extract account type from account name."""
        if not account:
            return "unknown"
        
        account = account.upper()
        
        if account.startswith(("BANK", "BK")):
            return "bank"
        elif account.startswith(("BROKER", "BR")):
            return "broker"
        elif account.startswith(("CLIENT", "CL")):
            return "client"
        elif account.startswith(("FUND", "FD")):
            return "fund"
        
        return "other"
    
    def _determine_probable_cause(self, exceptions: List[ReconException]) -> str:
        """Determine most probable cause for cluster."""
        cause_counts = defaultdict(int)
        
        for exception in exceptions:
            cause = self._extract_cause_code(exception)
            cause_counts[cause] += 1
        
        # Return most common cause
        if cause_counts:
            return max(cause_counts.items(), key=lambda x: x[1])[0]
        
        return "unknown"
    
    def _determine_cluster_severity(self, exceptions: List[ReconException]) -> str:
        """Determine severity level for cluster."""
        severity_scores = [self._get_exception_severity_score(exc) for exc in exceptions]
        avg_severity = sum(severity_scores) / len(severity_scores)
        
        if avg_severity >= 8:
            return "CRITICAL"
        elif avg_severity >= 6:
            return "HIGH"
        elif avg_severity >= 4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_exception_severity_score(self, exception: ReconException) -> int:
        """Get severity score for exception (1-10)."""
        score = 5  # Base score
        
        # Adjust based on exception type
        if hasattr(exception.exception_type, 'value'):
            exc_type = exception.exception_type.value
        else:
            exc_type = str(exception.exception_type)
        
        if exc_type == "PRICE_BREAK":
            score += 2
        elif exc_type == "QTY_BREAK":
            score += 1
        elif exc_type == "MISSING_EXTERNAL":
            score += 3
        elif exc_type == "MISSING_INTERNAL":
            score += 2
        
        # Adjust based on amounts involved
        if hasattr(exception, 'internal_qty') and exception.internal_qty:
            if exception.internal_qty > 1000000:  # Large notional
                score += 2
            elif exception.internal_qty > 100000:
                score += 1
        
        return min(score, 10)  # Cap at 10
    
    def _get_severity_priority(self, severity: str) -> int:
        """Get priority for severity level (higher = more severe)."""
        priorities = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }
        return priorities.get(severity, 0)
    
    def _calculate_average_impact(self, exceptions: List[ReconException]) -> float:
        """Calculate average financial impact of exceptions."""
        impacts = []
        
        for exception in exceptions:
            if hasattr(exception, 'internal_qty') and exception.internal_qty:
                impacts.append(abs(exception.internal_qty))
            elif hasattr(exception, 'external_qty') and exception.external_qty:
                impacts.append(abs(exception.external_qty))
        
        return sum(impacts) / len(impacts) if impacts else 0.0
    
    def _calculate_time_span(self, exceptions: List[ReconException]) -> Dict[str, Any]:
        """Calculate time span of exceptions in cluster."""
        # This would analyze timestamps if available
        return {
            "earliest": None,
            "latest": None,
            "span_hours": 0
        }
    
    def _analyze_geographic_spread(self, exceptions: List[ReconException]) -> Dict[str, int]:
        """Analyze geographic spread of exceptions."""
        # This would analyze geographic distribution if location data available
        return {
            "regions": 1,
            "countries": 1,
            "exchanges": 1
        }
    
    def _extract_clustering_features(self, exceptions: List[ReconException]) -> List[str]:
        """Extract key features that led to clustering."""
        features = set()
        
        for exception in exceptions:
            if hasattr(exception.exception_type, 'value'):
                features.add(f"type:{exception.exception_type.value}")
            
            if exception.symbol:
                product_type = self._extract_product_type(exception.symbol)
                features.add(f"product:{product_type}")
            
            cause = self._extract_cause_code(exception)
            features.add(f"cause:{cause}")
        
        return sorted(list(features))
