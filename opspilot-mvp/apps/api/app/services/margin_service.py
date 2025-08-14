"""Margin analysis service integrating SPAN parsing and delta narratives."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
from pathlib import Path

from sqlalchemy.orm import Session
from app.models.span import SpanSnapshot
from app.intelligence.margin.span_parser import SPANParser, MarginComponents
from app.intelligence.margin.delta_explainer import DeltaExplainer, MarginDelta
from app.publication.reports.margin_delta_report import MarginDeltaReport

logger = logging.getLogger(__name__)


class MarginService:
    """Service for comprehensive margin analysis and reporting."""
    
    def __init__(self, db: Session):
        self.db = db
        self.span_parser = SPANParser()
        self.delta_explainer = DeltaExplainer()
        self.report_generator = MarginDeltaReport()
    
    def process_span_file(
        self, 
        file_path: str, 
        as_of_date: Optional[date] = None
    ) -> List[MarginComponents]:
        """
        Process SPAN file and store margin components.
        
        Args:
            file_path: Path to SPAN CSV file
            as_of_date: Analysis date (defaults to today)
            
        Returns:
            List of parsed margin components
        """
        try:
            if not as_of_date:
                as_of_date = date.today()
            
            logger.info(f"Processing SPAN file: {file_path} for {as_of_date}")
            
            # Parse SPAN file
            components = self.span_parser.parse_span_file(file_path, as_of_date)
            
            # Store in database
            self._store_span_snapshots(components)
            
            logger.info(f"Processed {len(components)} margin components")
            return components
            
        except Exception as e:
            logger.error(f"Error processing SPAN file {file_path}: {e}")
            raise
    
    def analyze_margin_deltas(
        self,
        analysis_date: date,
        prior_date: Optional[date] = None,
        account_filter: Optional[str] = None,
        product_filter: Optional[str] = None,
        min_threshold: float = 500.0
    ) -> List[MarginDelta]:
        """
        Analyze margin deltas between two periods with narratives.
        
        Args:
            analysis_date: Current analysis date
            prior_date: Prior comparison date (defaults to previous day)
            account_filter: Optional account filter
            product_filter: Optional product filter
            min_threshold: Minimum delta threshold for significance
            
        Returns:
            List of margin deltas with narratives
        """
        try:
            if not prior_date:
                prior_date = analysis_date - timedelta(days=1)
            
            logger.info(f"Analyzing margin deltas: {prior_date} -> {analysis_date}")
            
            # Load margin components for both periods
            current_components = self._load_margin_components(
                analysis_date, account_filter, product_filter
            )
            
            prior_components = self._load_margin_components(
                prior_date, account_filter, product_filter
            )
            
            # Analyze deltas
            deltas = self.delta_explainer.analyze_deltas(
                prior_components, current_components
            )
            
            # Filter by threshold
            significant_deltas = [
                delta for delta in deltas 
                if abs(delta.total_delta) >= min_threshold
            ]
            
            logger.info(f"Found {len(significant_deltas)} significant margin deltas")
            return significant_deltas
            
        except Exception as e:
            logger.error(f"Error analyzing margin deltas: {e}")
            raise
    
    def generate_margin_report(
        self,
        deltas: List[MarginDelta],
        report_type: str = "detailed_analysis",
        output_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate comprehensive margin delta report.
        
        Args:
            deltas: List of margin deltas
            report_type: Type of report to generate
            output_path: Optional output file path
            **kwargs: Additional report parameters
            
        Returns:
            Generated report data
        """
        try:
            logger.info(f"Generating {report_type} report for {len(deltas)} deltas")
            
            report = self.report_generator.generate_report(
                deltas, report_type, output_path, **kwargs
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating margin report: {e}")
            raise
    
    def get_margin_alerts(
        self,
        threshold: float = 5000.0,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get margin change alerts for significant movements.
        
        Args:
            threshold: Alert threshold in dollars
            days_back: Number of days to analyze
            
        Returns:
            List of margin alerts with narratives
        """
        try:
            alerts = []
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            current_date = start_date
            while current_date <= end_date:
                try:
                    deltas = self.analyze_margin_deltas(
                        current_date, min_threshold=threshold
                    )
                    
                    for delta in deltas:
                        if abs(delta.total_delta) >= threshold:
                            alerts.append({
                                "alert_date": current_date.isoformat(),
                                "account": delta.account,
                                "product": delta.product,
                                "delta": float(delta.total_delta),
                                "delta_pct": delta.total_delta_pct,
                                "narrative": delta.narrative,
                                "primary_driver": delta.primary_driver.value,
                                "severity": self._calculate_alert_severity(
                                    delta.total_delta, threshold
                                )
                            })
                
                except Exception as e:
                    logger.warning(f"No data for {current_date}: {e}")
                
                current_date += timedelta(days=1)
            
            # Sort by severity and delta size
            alerts.sort(key=lambda x: (x["severity"], abs(x["delta"])), reverse=True)
            
            return alerts[:50]  # Return top 50 alerts
            
        except Exception as e:
            logger.error(f"Error getting margin alerts: {e}")
            raise
    
    def export_margin_data(
        self,
        analysis_date: date,
        format: str = "csv",
        account_filter: Optional[str] = None,
        product_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export margin delta data with narratives.
        
        Args:
            analysis_date: Analysis date
            format: Export format (csv or json)
            account_filter: Optional account filter
            product_filter: Optional product filter
            
        Returns:
            Export data in requested format
        """
        try:
            # Analyze deltas
            deltas = self.analyze_margin_deltas(
                analysis_date, 
                account_filter=account_filter,
                product_filter=product_filter,
                min_threshold=0  # Include all deltas for export
            )
            
            # Generate export report
            export_data = self.report_generator.generate_report(
                deltas, "csv_export" if format == "csv" else "detailed_analysis"
            )
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting margin data: {e}")
            raise
    
    def _store_span_snapshots(self, components: List[MarginComponents]):
        """Store margin components as SPAN snapshots in database."""
        try:
            for component in components:
                # Check if snapshot already exists
                existing = self.db.query(SpanSnapshot).filter(
                    SpanSnapshot.account == component.account,
                    SpanSnapshot.product == component.product,
                    SpanSnapshot.as_of_date == component.as_of_date
                ).first()
                
                if existing:
                    # Update existing snapshot
                    existing.scan_risk = float(component.scan_risk)
                    existing.total_margin = float(component.total_margin)
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new snapshot
                    snapshot = SpanSnapshot(
                        account=component.account,
                        product=component.product,
                        as_of_date=component.as_of_date,
                        scan_risk=float(component.scan_risk),
                        total_margin=float(component.total_margin),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.db.add(snapshot)
            
            self.db.commit()
            logger.info(f"Stored {len(components)} SPAN snapshots")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing SPAN snapshots: {e}")
            raise
    
    def _load_margin_components(
        self,
        as_of_date: date,
        account_filter: Optional[str] = None,
        product_filter: Optional[str] = None
    ) -> Dict[Tuple[str, str], MarginComponents]:
        """Load margin components from database for specified date."""
        try:
            query = self.db.query(SpanSnapshot).filter(
                SpanSnapshot.as_of_date == as_of_date
            )
            
            if account_filter:
                query = query.filter(SpanSnapshot.account == account_filter)
            
            if product_filter:
                query = query.filter(SpanSnapshot.product == product_filter)
            
            snapshots = query.all()
            
            components = {}
            for snapshot in snapshots:
                key = (snapshot.account, snapshot.product)
                
                component = MarginComponents(
                    account=snapshot.account,
                    product=snapshot.product,
                    series=snapshot.product,  # Use product as series
                    as_of_date=snapshot.as_of_date,
                    scan_risk=Decimal(str(snapshot.scan_risk)),
                    inter_spread_charge=Decimal("0"),  # Not stored separately
                    short_opt_minimum=Decimal("0"),
                    long_opt_credit=Decimal("0"),
                    net_premium=Decimal("0"),
                    add_on_margin=Decimal("0"),
                    total_margin=Decimal(str(snapshot.total_margin)),
                    net_position=0  # Not stored in current model
                )
                
                components[key] = component
            
            return components
            
        except Exception as e:
            logger.error(f"Error loading margin components for {as_of_date}: {e}")
            raise
    
    def _calculate_alert_severity(self, delta: float, threshold: float) -> int:
        """Calculate alert severity level (1-5)."""
        abs_delta = abs(delta)
        
        if abs_delta >= threshold * 5:
            return 5  # Critical
        elif abs_delta >= threshold * 3:
            return 4  # High
        elif abs_delta >= threshold * 2:
            return 3  # Medium
        elif abs_delta >= threshold * 1.5:
            return 2  # Low
        else:
            return 1  # Info
