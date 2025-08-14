"""Margin delta report generation with narratives."""

from typing import Dict, List, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import pandas as pd
from pathlib import Path
import logging

from app.intelligence.margin.delta_explainer import MarginDelta, DeltaExplainer
from app.intelligence.margin.span_parser import MarginComponents

logger = logging.getLogger(__name__)


class MarginDeltaReport:
    """Generates comprehensive margin delta reports with narratives."""
    
    def __init__(self):
        self.report_templates = {
            "executive_summary": self._generate_executive_summary,
            "detailed_analysis": self._generate_detailed_analysis,
            "exception_feed": self._generate_exception_feed,
            "csv_export": self._generate_csv_export
        }
    
    def generate_report(
        self,
        deltas: List[MarginDelta],
        report_type: str = "detailed_analysis",
        output_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate margin delta report in specified format.
        
        Args:
            deltas: List of margin deltas with narratives
            report_type: Type of report to generate
            output_path: Optional file path for output
            **kwargs: Additional parameters for report generation
            
        Returns:
            Report data dictionary
        """
        if report_type not in self.report_templates:
            raise ValueError(f"Unknown report type: {report_type}")
        
        logger.info(f"Generating {report_type} report for {len(deltas)} deltas")
        
        # Generate report data
        generator = self.report_templates[report_type]
        report_data = generator(deltas, **kwargs)
        
        # Add metadata
        report_data["metadata"] = {
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "total_deltas": len(deltas),
            "significant_deltas": len([d for d in deltas if abs(d.total_delta) >= 500]),
            "generation_params": kwargs
        }
        
        # Save to file if path provided
        if output_path:
            self._save_report(report_data, output_path, report_type)
        
        return report_data
    
    def _generate_executive_summary(self, deltas: List[MarginDelta], **kwargs) -> Dict[str, Any]:
        """Generate executive summary report."""
        if not deltas:
            return {
                "summary": "No significant margin changes detected.",
                "key_metrics": {},
                "top_changes": [],
                "recommendations": []
            }
        
        # Calculate key metrics
        total_increase = sum(d.total_delta for d in deltas if d.total_delta > 0)
        total_decrease = sum(abs(d.total_delta) for d in deltas if d.total_delta < 0)
        net_change = sum(d.total_delta for d in deltas)
        
        accounts_affected = len(set(d.account for d in deltas))
        products_affected = len(set(d.product for d in deltas))
        
        # Top 5 changes by absolute delta
        top_changes = sorted(deltas, key=lambda x: abs(x.total_delta), reverse=True)[:5]
        
        # Generate summary narrative
        if net_change > 10000:
            summary = f"Portfolio margin increased by ${net_change:,.0f} across {products_affected} products and {accounts_affected} accounts."
        elif net_change < -10000:
            summary = f"Portfolio margin decreased by ${abs(net_change):,.0f} across {products_affected} products and {accounts_affected} accounts."
        else:
            summary = f"Portfolio margin relatively stable with ${abs(net_change):,.0f} net change across {products_affected} products."
        
        # Generate recommendations
        recommendations = []
        
        if any(abs(d.total_delta) > 50000 for d in deltas):
            recommendations.append("Review positions with margin changes exceeding $50,000")
        
        if len([d for d in deltas if d.primary_driver.value == "position_change"]) > 5:
            recommendations.append("Multiple position changes detected - verify trade execution")
        
        if len([d for d in deltas if d.primary_driver.value == "volatility"]) > 10:
            recommendations.append("Market volatility impacting multiple positions - consider risk management")
        
        return {
            "summary": summary,
            "key_metrics": {
                "net_change": float(net_change),
                "total_increase": float(total_increase),
                "total_decrease": float(total_decrease),
                "accounts_affected": accounts_affected,
                "products_affected": products_affected,
                "largest_single_change": float(max(deltas, key=lambda x: abs(x.total_delta)).total_delta)
            },
            "top_changes": [
                {
                    "account": d.account,
                    "product": d.product,
                    "delta": float(d.total_delta),
                    "narrative": d.narrative
                }
                for d in top_changes
            ],
            "recommendations": recommendations
        }
    
    def _generate_detailed_analysis(self, deltas: List[MarginDelta], **kwargs) -> Dict[str, Any]:
        """Generate detailed analysis report."""
        
        # Group deltas by various dimensions
        by_account = {}
        by_product = {}
        by_driver = {}
        
        for delta in deltas:
            # By account
            if delta.account not in by_account:
                by_account[delta.account] = []
            by_account[delta.account].append(delta)
            
            # By product
            if delta.product not in by_product:
                by_product[delta.product] = []
            by_product[delta.product].append(delta)
            
            # By primary driver
            driver = delta.primary_driver.value
            if driver not in by_driver:
                by_driver[driver] = []
            by_driver[driver].append(delta)
        
        # Calculate statistics for each grouping
        account_analysis = {}
        for account, account_deltas in by_account.items():
            net_change = sum(d.total_delta for d in account_deltas)
            account_analysis[account] = {
                "net_change": float(net_change),
                "products_affected": len(account_deltas),
                "largest_change": float(max(account_deltas, key=lambda x: abs(x.total_delta)).total_delta),
                "narratives": [d.narrative for d in account_deltas[:3]]  # Top 3
            }
        
        product_analysis = {}
        for product, product_deltas in by_product.items():
            net_change = sum(d.total_delta for d in product_deltas)
            product_analysis[product] = {
                "net_change": float(net_change),
                "accounts_affected": len(product_deltas),
                "avg_change": float(net_change / len(product_deltas)),
                "primary_drivers": list(set(d.primary_driver.value for d in product_deltas))
            }
        
        driver_analysis = {}
        for driver, driver_deltas in by_driver.items():
            total_impact = sum(abs(d.total_delta) for d in driver_deltas)
            driver_analysis[driver] = {
                "total_impact": float(total_impact),
                "occurrence_count": len(driver_deltas),
                "avg_impact": float(total_impact / len(driver_deltas)),
                "description": self._get_driver_description(driver)
            }
        
        return {
            "analysis_summary": {
                "total_deltas_analyzed": len(deltas),
                "accounts_analyzed": len(by_account),
                "products_analyzed": len(by_product),
                "primary_drivers_identified": len(by_driver)
            },
            "account_analysis": account_analysis,
            "product_analysis": product_analysis,
            "driver_analysis": driver_analysis,
            "detailed_deltas": [delta.to_dict() for delta in deltas]
        }
    
    def _generate_exception_feed(self, deltas: List[MarginDelta], threshold: float = 5000, **kwargs) -> Dict[str, Any]:
        """Generate exception feed for margin changes exceeding threshold."""
        
        # Filter deltas exceeding threshold
        exceptions = [d for d in deltas if abs(d.total_delta) >= threshold]
        
        # Sort by absolute delta size
        exceptions.sort(key=lambda x: abs(x.total_delta), reverse=True)
        
        exception_records = []
        for delta in exceptions:
            record = {
                "exception_id": f"MARGIN_{delta.account}_{delta.product}_{delta.current_components.as_of_date.strftime('%Y%m%d')}",
                "account": delta.account,
                "product": delta.product,
                "delta": float(delta.total_delta),
                "delta_pct": delta.total_delta_pct,
                "narrative": delta.narrative,
                "primary_driver": delta.primary_driver.value,
                "severity": self._calculate_exception_severity(delta.total_delta, threshold),
                "requires_review": abs(delta.total_delta) >= threshold * 2,
                "component_breakdown": {
                    name: {
                        "delta": float(comp.absolute_delta),
                        "contribution_pct": comp.contribution_pct
                    }
                    for name, comp in delta.component_deltas.items()
                    if comp.is_significant
                },
                "as_of_date": delta.current_components.as_of_date.isoformat()
            }
            exception_records.append(record)
        
        return {
            "threshold": threshold,
            "total_exceptions": len(exception_records),
            "critical_exceptions": len([r for r in exception_records if r["severity"] >= 4]),
            "exceptions_requiring_review": len([r for r in exception_records if r["requires_review"]]),
            "exception_records": exception_records
        }
    
    def _generate_csv_export(self, deltas: List[MarginDelta], **kwargs) -> Dict[str, Any]:
        """Generate CSV export format."""
        
        csv_records = []
        for delta in deltas:
            base_record = {
                "account": delta.account,
                "product": delta.product,
                "series": delta.series,
                "as_of_date": delta.current_components.as_of_date.isoformat(),
                "prior_total_margin": float(delta.prior_components.total_margin) if delta.prior_components else 0,
                "current_total_margin": float(delta.current_components.total_margin),
                "total_delta": float(delta.total_delta),
                "total_delta_pct": delta.total_delta_pct,
                "primary_driver": delta.primary_driver.value,
                "narrative": delta.narrative,
                "is_significant": abs(delta.total_delta) >= 500
            }
            
            # Add component deltas
            for comp_name, comp_delta in delta.component_deltas.items():
                base_record[f"{comp_name}_prior"] = float(comp_delta.prior_value)
                base_record[f"{comp_name}_current"] = float(comp_delta.current_value)
                base_record[f"{comp_name}_delta"] = float(comp_delta.absolute_delta)
                base_record[f"{comp_name}_delta_pct"] = comp_delta.percent_delta
                base_record[f"{comp_name}_contribution"] = comp_delta.contribution_pct
            
            csv_records.append(base_record)
        
        return {
            "format": "csv",
            "records": csv_records,
            "column_headers": list(csv_records[0].keys()) if csv_records else [],
            "record_count": len(csv_records)
        }
    
    def _save_report(self, report_data: Dict[str, Any], output_path: str, report_type: str):
        """Save report to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if report_type == "csv_export":
                # Save as CSV
                df = pd.DataFrame(report_data["records"])
                df.to_csv(output_file, index=False)
                logger.info(f"CSV report saved to {output_file}")
            else:
                # Save as JSON
                import json
                with open(output_file, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
                logger.info(f"JSON report saved to {output_file}")
                
        except Exception as e:
            logger.error(f"Failed to save report to {output_path}: {e}")
    
    def _get_driver_description(self, driver: str) -> str:
        """Get description for primary driver type."""
        descriptions = {
            "scan_risk": "Changes in initial margin requirements due to risk parameter updates",
            "position_change": "Margin changes due to position size adjustments",
            "volatility": "Market volatility parameter changes affecting margin calculations",
            "spread_charge": "Inter-commodity spread charge adjustments",
            "option_premium": "Option premium and minimum margin requirement changes",
            "new_product": "New positions established requiring initial margin",
            "closed_product": "Positions closed releasing margin requirements"
        }
        return descriptions.get(driver, driver.replace("_", " ").title())
    
    def _calculate_exception_severity(self, delta: float, threshold: float) -> int:
        """Calculate exception severity (1-5 scale)."""
        abs_delta = abs(delta)
        
        if abs_delta >= threshold * 10:
            return 5  # Critical
        elif abs_delta >= threshold * 5:
            return 4  # High
        elif abs_delta >= threshold * 3:
            return 3  # Medium
        elif abs_delta >= threshold * 2:
            return 2  # Low
        else:
            return 1  # Info
    
    def generate_daily_summary_email(self, deltas: List[MarginDelta]) -> str:
        """Generate daily summary email content."""
        if not deltas:
            return """
            Daily Margin Summary
            
            No significant margin changes detected today.
            
            All positions within normal tolerance levels.
            """
        
        # Generate executive summary
        exec_summary = self._generate_executive_summary(deltas)
        
        # Create email content
        email_content = f"""
        Daily Margin Summary - {datetime.now().strftime('%Y-%m-%d')}
        
        EXECUTIVE SUMMARY
        {exec_summary['summary']}
        
        KEY METRICS
        • Net Change: ${exec_summary['key_metrics']['net_change']:,.0f}
        • Accounts Affected: {exec_summary['key_metrics']['accounts_affected']}
        • Products Affected: {exec_summary['key_metrics']['products_affected']}
        • Largest Single Change: ${exec_summary['key_metrics']['largest_single_change']:,.0f}
        
        TOP CHANGES
        """
        
        for i, change in enumerate(exec_summary['top_changes'][:5], 1):
            email_content += f"""
        {i}. {change['account']} / {change['product']}: ${change['delta']:,.0f}
           {change['narrative']}
        """
        
        if exec_summary['recommendations']:
            email_content += "\n\nRECOMMENDATIONS\n"
            for rec in exec_summary['recommendations']:
                email_content += f"• {rec}\n"
        
        return email_content.strip()
