"""Margin analysis API endpoints with delta narratives."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import logging

from app.db.session import get_db
from app.models.span import SpanSnapshot
from app.intelligence.margin.span_parser import SPANParser, MarginComponents
from app.intelligence.margin.delta_explainer import DeltaExplainer, MarginDelta
from app.services.span_service import SpanService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/margin/deltas")
async def get_margin_deltas(
    account: Optional[str] = Query(None, description="Filter by account"),
    product: Optional[str] = Query(None, description="Filter by product"),
    as_of_date: Optional[str] = Query(None, description="Analysis date (YYYY-MM-DD)"),
    min_delta: Optional[float] = Query(500, description="Minimum delta threshold"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get margin deltas with narratives for specified criteria.
    
    Returns detailed margin component analysis with plain-English explanations
    for why margin requirements changed between periods.
    """
    try:
        # Parse and validate date
        if as_of_date:
            analysis_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
        else:
            analysis_date = date.today()
        
        prior_date = analysis_date - timedelta(days=1)
        
        logger.info(f"Analyzing margin deltas: {prior_date} -> {analysis_date}")
        
        # Load SPAN snapshots for both periods
        current_snapshots = db.query(SpanSnapshot).filter(
            SpanSnapshot.as_of_date == analysis_date
        )
        
        prior_snapshots = db.query(SpanSnapshot).filter(
            SpanSnapshot.as_of_date == prior_date
        )
        
        # Apply filters
        if account:
            current_snapshots = current_snapshots.filter(SpanSnapshot.account == account)
            prior_snapshots = prior_snapshots.filter(SpanSnapshot.account == account)
        
        if product:
            current_snapshots = current_snapshots.filter(SpanSnapshot.product == product)
            prior_snapshots = prior_snapshots.filter(SpanSnapshot.product == product)
        
        current_data = current_snapshots.all()
        prior_data = prior_snapshots.all()
        
        if not current_data:
            raise HTTPException(
                status_code=404,
                detail=f"No SPAN data found for {analysis_date}"
            )
        
        # Convert to margin components format
        current_components = _convert_snapshots_to_components(current_data)
        prior_components = _convert_snapshots_to_components(prior_data)
        
        # Analyze deltas
        explainer = DeltaExplainer()
        deltas = explainer.analyze_deltas(prior_components, current_components)
        
        # Filter by minimum delta
        if min_delta:
            deltas = [d for d in deltas if abs(d.total_delta) >= min_delta]
        
        # Generate portfolio summary
        portfolio_summary = explainer.generate_portfolio_summary(deltas)
        
        return {
            "analysis_date": analysis_date.isoformat(),
            "prior_date": prior_date.isoformat(),
            "filters": {
                "account": account,
                "product": product,
                "min_delta": min_delta
            },
            "portfolio_summary": portfolio_summary,
            "deltas": [delta.to_dict() for delta in deltas],
            "total_deltas": len(deltas)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error analyzing margin deltas: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/margin/narratives/{account}/{product}")
async def get_margin_narrative(
    account: str,
    product: str,
    as_of_date: Optional[str] = Query(None, description="Analysis date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed margin narrative for specific account/product combination.
    
    Returns comprehensive analysis including component breakdowns,
    change drivers, and plain-English explanations.
    """
    try:
        # Parse date
        if as_of_date:
            analysis_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
        else:
            analysis_date = date.today()
        
        prior_date = analysis_date - timedelta(days=1)
        
        # Load specific snapshots
        current_snapshot = db.query(SpanSnapshot).filter(
            SpanSnapshot.as_of_date == analysis_date,
            SpanSnapshot.account == account,
            SpanSnapshot.product == product
        ).first()
        
        prior_snapshot = db.query(SpanSnapshot).filter(
            SpanSnapshot.as_of_date == prior_date,
            SpanSnapshot.account == account,
            SpanSnapshot.product == product
        ).first()
        
        if not current_snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"No margin data found for {account}/{product} on {analysis_date}"
            )
        
        # Convert to margin components
        current_component = _convert_snapshot_to_component(current_snapshot)
        prior_component = _convert_snapshot_to_component(prior_snapshot) if prior_snapshot else None
        
        # Analyze delta
        explainer = DeltaExplainer()
        
        if prior_component:
            prior_components = {(account, product): prior_component}
            current_components = {(account, product): current_component}
            deltas = explainer.analyze_deltas(prior_components, current_components)
        else:
            # New product case
            deltas = [explainer._analyze_new_product(account, product, current_component)]
        
        if not deltas:
            return {
                "account": account,
                "product": product,
                "analysis_date": analysis_date.isoformat(),
                "narrative": "No significant margin changes detected.",
                "delta_details": None
            }
        
        delta = deltas[0]
        
        return {
            "account": account,
            "product": product,
            "analysis_date": analysis_date.isoformat(),
            "prior_date": prior_date.isoformat(),
            "narrative": delta.narrative,
            "delta_details": delta.to_dict(),
            "component_breakdown": {
                name: {
                    "description": _get_component_description(name),
                    "prior": float(comp.prior_value),
                    "current": float(comp.current_value),
                    "change": float(comp.absolute_delta),
                    "change_pct": comp.percent_delta,
                    "contribution": comp.contribution_pct
                }
                for name, comp in delta.component_deltas.items()
                if comp.is_significant
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error getting margin narrative: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/margin/export")
async def export_margin_deltas(
    account: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    as_of_date: Optional[str] = Query(None),
    format: str = Query("csv", description="Export format: csv or json"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Export margin deltas with narratives in CSV or JSON format.
    
    Includes all delta components and plain-English explanations
    suitable for reporting and analysis.
    """
    try:
        # Get margin deltas (reuse logic from get_margin_deltas)
        delta_response = await get_margin_deltas(
            account=account,
            product=product,
            as_of_date=as_of_date,
            min_delta=0,  # Include all deltas for export
            db=db
        )
        
        deltas = delta_response["deltas"]
        
        if format.lower() == "json":
            return {
                "format": "json",
                "data": delta_response,
                "export_timestamp": datetime.utcnow().isoformat(),
                "record_count": len(deltas)
            }
        
        # CSV format
        csv_data = []
        for delta in deltas:
            row = {
                "account": delta["account"],
                "product": delta["product"],
                "series": delta["series"],
                "prior_total_margin": delta["prior_total"],
                "current_total_margin": delta["current_total"],
                "total_delta": delta["total_delta"],
                "total_delta_pct": delta["total_delta_pct"],
                "primary_driver": delta["primary_driver"],
                "narrative": delta["narrative"],
                "is_significant": delta["is_significant"]
            }
            
            # Add component deltas
            for comp_name, comp_data in delta["component_deltas"].items():
                row[f"{comp_name}_prior"] = comp_data["prior"]
                row[f"{comp_name}_current"] = comp_data["current"]
                row[f"{comp_name}_delta"] = comp_data["delta"]
                row[f"{comp_name}_delta_pct"] = comp_data["delta_pct"]
            
            csv_data.append(row)
        
        return {
            "format": "csv",
            "data": csv_data,
            "export_timestamp": datetime.utcnow().isoformat(),
            "record_count": len(csv_data),
            "columns": list(csv_data[0].keys()) if csv_data else []
        }
        
    except Exception as e:
        logger.error(f"Error exporting margin deltas: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/margin/alerts")
async def get_margin_alerts(
    threshold: float = Query(5000, description="Alert threshold in dollars"),
    days_back: int = Query(7, description="Days to look back for alerts"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get margin change alerts for positions exceeding threshold.
    
    Returns list of significant margin changes that may require attention,
    with narratives explaining the changes.
    """
    try:
        alerts = []
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        # Analyze each day in the range
        current_date = start_date
        while current_date <= end_date:
            prior_date = current_date - timedelta(days=1)
            
            # Get deltas for this date
            try:
                delta_response = await get_margin_deltas(
                    as_of_date=current_date.isoformat(),
                    min_delta=threshold,
                    db=db
                )
                
                # Add alerts for significant changes
                for delta in delta_response["deltas"]:
                    if abs(delta["total_delta"]) >= threshold:
                        alerts.append({
                            "alert_date": current_date.isoformat(),
                            "account": delta["account"],
                            "product": delta["product"],
                            "delta": delta["total_delta"],
                            "delta_pct": delta["total_delta_pct"],
                            "narrative": delta["narrative"],
                            "severity": _calculate_alert_severity(delta["total_delta"], threshold)
                        })
                        
            except HTTPException:
                # Skip dates with no data
                pass
            
            current_date += timedelta(days=1)
        
        # Sort by severity and delta size
        alerts.sort(key=lambda x: (x["severity"], abs(x["delta"])), reverse=True)
        
        return {
            "threshold": threshold,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "alerts": alerts[:50],  # Limit to top 50 alerts
            "total_alerts": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Error getting margin alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _convert_snapshots_to_components(snapshots: List[SpanSnapshot]) -> Dict[tuple, MarginComponents]:
    """Convert SpanSnapshot objects to MarginComponents format."""
    components = {}
    
    for snapshot in snapshots:
        key = (snapshot.account, snapshot.product)
        
        # Create margin component (simplified from full SPAN data)
        component = MarginComponents(
            account=snapshot.account,
            product=snapshot.product,
            series=snapshot.product,  # Use product as series for now
            as_of_date=snapshot.as_of_date,
            scan_risk=snapshot.scan_risk,
            inter_spread_charge=snapshot.total_margin - snapshot.scan_risk,  # Approximate
            short_opt_minimum=0,  # Not available in current model
            long_opt_credit=0,    # Not available in current model
            net_premium=0,        # Not available in current model
            add_on_margin=0,      # Not available in current model
            total_margin=snapshot.total_margin,
            net_position=0        # Not available in current model
        )
        
        components[key] = component
    
    return components


def _convert_snapshot_to_component(snapshot: SpanSnapshot) -> MarginComponents:
    """Convert single SpanSnapshot to MarginComponents."""
    return MarginComponents(
        account=snapshot.account,
        product=snapshot.product,
        series=snapshot.product,
        as_of_date=snapshot.as_of_date,
        scan_risk=snapshot.scan_risk,
        inter_spread_charge=snapshot.total_margin - snapshot.scan_risk,
        short_opt_minimum=0,
        long_opt_credit=0,
        net_premium=0,
        add_on_margin=0,
        total_margin=snapshot.total_margin,
        net_position=0
    )


def _get_component_description(component_name: str) -> str:
    """Get human-readable description for margin component."""
    descriptions = {
        "scan_risk": "Initial margin requirement based on worst-case scenario analysis",
        "inter_spread_charge": "Additional margin for inter-commodity spread positions",
        "short_opt_minimum": "Minimum margin requirement for short option positions",
        "long_opt_credit": "Margin credit for long option positions",
        "net_premium": "Net option premium adjustments to margin",
        "add_on_margin": "Additional margin requirements for specific risk factors"
    }
    
    return descriptions.get(component_name, component_name.replace("_", " ").title())


def _calculate_alert_severity(delta: float, threshold: float) -> int:
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
