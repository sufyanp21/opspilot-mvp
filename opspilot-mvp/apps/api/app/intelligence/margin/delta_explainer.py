"""SPAN margin delta explainer with plain-English narratives."""

from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import logging

from app.intelligence.margin.span_parser import MarginComponents

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of margin changes."""
    SCAN_RISK = "scan_risk"
    POSITION_CHANGE = "position_change"
    VOLATILITY = "volatility"
    SPREAD_CHARGE = "spread_charge"
    OPTION_PREMIUM = "option_premium"
    NEW_PRODUCT = "new_product"
    CLOSED_PRODUCT = "closed_product"


@dataclass
class DeltaComponent:
    """Individual component of a margin delta."""
    component_name: str
    prior_value: Decimal
    current_value: Decimal
    absolute_delta: Decimal
    percent_delta: float
    contribution_pct: float
    
    @property
    def is_significant(self) -> bool:
        """Check if delta is significant (>$500 or >2%)."""
        return abs(self.absolute_delta) >= 500 or abs(self.percent_delta) >= 2.0


@dataclass
class MarginDelta:
    """Complete margin delta analysis for an account/product."""
    account: str
    product: str
    series: str
    
    # Prior and current components
    prior_components: Optional[MarginComponents]
    current_components: MarginComponents
    
    # Delta analysis
    total_delta: Decimal
    total_delta_pct: float
    component_deltas: Dict[str, DeltaComponent]
    
    # Narrative analysis
    primary_driver: ChangeType
    top_contributors: List[DeltaComponent]
    narrative: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "account": self.account,
            "product": self.product,
            "series": self.series,
            "total_delta": float(self.total_delta),
            "total_delta_pct": self.total_delta_pct,
            "prior_total": float(self.prior_components.total_margin) if self.prior_components else 0,
            "current_total": float(self.current_components.total_margin),
            "component_deltas": {
                name: {
                    "prior": float(delta.prior_value),
                    "current": float(delta.current_value),
                    "delta": float(delta.absolute_delta),
                    "delta_pct": delta.percent_delta,
                    "contribution_pct": delta.contribution_pct
                }
                for name, delta in self.component_deltas.items()
            },
            "primary_driver": self.primary_driver,
            "narrative": self.narrative,
            "is_significant": abs(self.total_delta) >= 500 or abs(self.total_delta_pct) >= 2.0
        }


class DeltaExplainer:
    """Generates plain-English explanations for SPAN margin deltas."""
    
    def __init__(self):
        self.significance_thresholds = {
            "absolute_min": Decimal("500"),  # Minimum $500 change
            "percent_min": 2.0,              # Minimum 2% change
            "pareto_threshold": 80.0         # Top contributors explain 80%
        }
        
        self.narrative_templates = {
            ChangeType.SCAN_RISK: [
                "Initial margin ↑${delta:,.0f} mainly due to higher scan risk on {product} (+${component_delta:,.0f}).",
                "Scan risk increased by ${component_delta:,.0f} on {product}, driving margin up ${delta:,.0f}.",
                "Higher volatility parameters increased {product} scan risk by ${component_delta:,.0f}."
            ],
            ChangeType.POSITION_CHANGE: [
                "Net contracts {position_change:+d} in {product} increased risk by ${delta:,.0f}.",
                "Position increase of {position_change:+d} contracts in {product} added ${delta:,.0f} margin.",
                "Expanded {product} position ({position_change:+d} contracts) drove margin up ${delta:,.0f}."
            ],
            ChangeType.VOLATILITY: [
                "Volatility parameters increased; margin +${delta:,.0f} with flat exposure.",
                "Market volatility adjustments increased margin by ${delta:,.0f} despite unchanged positions.",
                "SPAN parameter updates added ${delta:,.0f} to margin requirements."
            ],
            ChangeType.SPREAD_CHARGE: [
                "Inter-commodity spread charges increased by ${component_delta:,.0f}.",
                "Portfolio spread benefits reduced, adding ${component_delta:,.0f} to margin.",
                "Spread charge adjustments contributed ${component_delta:,.0f} to higher margin."
            ],
            ChangeType.OPTION_PREMIUM: [
                "Option premium adjustments changed margin by ${delta:,.0f}.",
                "Net option positions contributed ${component_delta:,.0f} to margin change.",
                "Option market movements adjusted margin by ${delta:,.0f}."
            ],
            ChangeType.NEW_PRODUCT: [
                "New {product} position established with ${delta:,.0f} initial margin.",
                "Added {product} exposure requiring ${delta:,.0f} additional margin.",
                "New {product} trades contributed ${delta:,.0f} to total margin."
            ],
            ChangeType.CLOSED_PRODUCT: [
                "Closed {product} position, releasing ${delta:,.0f} margin.",
                "{product} position eliminated, reducing margin by ${delta:,.0f}.",
                "Exit from {product} freed up ${delta:,.0f} in margin."
            ]
        }
    
    def analyze_deltas(
        self,
        prior_components: Dict[Tuple[str, str], MarginComponents],
        current_components: Dict[Tuple[str, str], MarginComponents]
    ) -> List[MarginDelta]:
        """
        Analyze margin deltas between two time periods.
        
        Args:
            prior_components: Previous day's margin components by (account, product)
            current_components: Current day's margin components by (account, product)
            
        Returns:
            List of MarginDelta objects with narratives
        """
        logger.info(f"Analyzing deltas: {len(prior_components)} prior, {len(current_components)} current")
        
        deltas = []
        all_keys = set(prior_components.keys()) | set(current_components.keys())
        
        for key in all_keys:
            account, product = key
            prior = prior_components.get(key)
            current = current_components.get(key)
            
            if current is None:
                # Product closed
                delta = self._analyze_closed_product(account, product, prior)
            elif prior is None:
                # New product
                delta = self._analyze_new_product(account, product, current)
            else:
                # Existing product with changes
                delta = self._analyze_existing_product(prior, current)
            
            if delta and self._is_significant_delta(delta):
                deltas.append(delta)
        
        # Sort by absolute delta size
        deltas.sort(key=lambda d: abs(d.total_delta), reverse=True)
        
        logger.info(f"Generated {len(deltas)} significant margin deltas")
        return deltas
    
    def _analyze_existing_product(
        self,
        prior: MarginComponents,
        current: MarginComponents
    ) -> Optional[MarginDelta]:
        """Analyze delta for existing product."""
        
        # Calculate total delta
        total_delta = current.total_margin - prior.total_margin
        
        if prior.total_margin == 0:
            total_delta_pct = 0.0
        else:
            total_delta_pct = float((total_delta / prior.total_margin) * 100)
        
        # Calculate component deltas
        component_deltas = self._calculate_component_deltas(prior, current, total_delta)
        
        # Identify primary driver and top contributors
        primary_driver, top_contributors = self._identify_primary_driver(
            prior, current, component_deltas
        )
        
        # Generate narrative
        narrative = self._generate_narrative(
            primary_driver, current.product, total_delta, 
            component_deltas, prior, current
        )
        
        return MarginDelta(
            account=current.account,
            product=current.product,
            series=current.series,
            prior_components=prior,
            current_components=current,
            total_delta=total_delta,
            total_delta_pct=total_delta_pct,
            component_deltas=component_deltas,
            primary_driver=primary_driver,
            top_contributors=top_contributors,
            narrative=narrative
        )
    
    def _analyze_new_product(
        self,
        account: str,
        product: str,
        current: MarginComponents
    ) -> MarginDelta:
        """Analyze delta for new product."""
        
        total_delta = current.total_margin
        
        # Create empty component deltas
        component_deltas = {}
        for component_name in ["scan_risk", "inter_spread_charge", "short_opt_minimum", 
                              "long_opt_credit", "net_premium", "add_on_margin"]:
            current_value = getattr(current, component_name, Decimal("0"))
            component_deltas[component_name] = DeltaComponent(
                component_name=component_name,
                prior_value=Decimal("0"),
                current_value=current_value,
                absolute_delta=current_value,
                percent_delta=100.0 if current_value > 0 else 0.0,
                contribution_pct=float((current_value / total_delta) * 100) if total_delta > 0 else 0.0
            )
        
        narrative = self._generate_narrative(
            ChangeType.NEW_PRODUCT, product, total_delta, 
            component_deltas, None, current
        )
        
        return MarginDelta(
            account=account,
            product=product,
            series=current.series,
            prior_components=None,
            current_components=current,
            total_delta=total_delta,
            total_delta_pct=100.0,
            component_deltas=component_deltas,
            primary_driver=ChangeType.NEW_PRODUCT,
            top_contributors=list(component_deltas.values())[:3],
            narrative=narrative
        )
    
    def _analyze_closed_product(
        self,
        account: str,
        product: str,
        prior: MarginComponents
    ) -> MarginDelta:
        """Analyze delta for closed product."""
        
        total_delta = -prior.total_margin
        
        # Create component deltas showing reduction
        component_deltas = {}
        for component_name in ["scan_risk", "inter_spread_charge", "short_opt_minimum", 
                              "long_opt_credit", "net_premium", "add_on_margin"]:
            prior_value = getattr(prior, component_name, Decimal("0"))
            component_deltas[component_name] = DeltaComponent(
                component_name=component_name,
                prior_value=prior_value,
                current_value=Decimal("0"),
                absolute_delta=-prior_value,
                percent_delta=-100.0 if prior_value > 0 else 0.0,
                contribution_pct=float((prior_value / prior.total_margin) * 100) if prior.total_margin > 0 else 0.0
            )
        
        narrative = self._generate_narrative(
            ChangeType.CLOSED_PRODUCT, product, total_delta, 
            component_deltas, prior, None
        )
        
        return MarginDelta(
            account=account,
            product=product,
            series=prior.series,
            prior_components=prior,
            current_components=None,
            total_delta=total_delta,
            total_delta_pct=-100.0,
            component_deltas=component_deltas,
            primary_driver=ChangeType.CLOSED_PRODUCT,
            top_contributors=list(component_deltas.values())[:3],
            narrative=narrative
        )
    
    def _calculate_component_deltas(
        self,
        prior: MarginComponents,
        current: MarginComponents,
        total_delta: Decimal
    ) -> Dict[str, DeltaComponent]:
        """Calculate deltas for each margin component."""
        
        component_deltas = {}
        component_names = [
            "scan_risk", "inter_spread_charge", "short_opt_minimum",
            "long_opt_credit", "net_premium", "add_on_margin"
        ]
        
        for component_name in component_names:
            prior_value = getattr(prior, component_name, Decimal("0"))
            current_value = getattr(current, component_name, Decimal("0"))
            absolute_delta = current_value - prior_value
            
            # Calculate percentage change
            if prior_value == 0:
                percent_delta = 100.0 if current_value > 0 else 0.0
            else:
                percent_delta = float((absolute_delta / prior_value) * 100)
            
            # Calculate contribution to total change
            if total_delta == 0:
                contribution_pct = 0.0
            else:
                contribution_pct = float((absolute_delta / total_delta) * 100)
            
            component_deltas[component_name] = DeltaComponent(
                component_name=component_name,
                prior_value=prior_value,
                current_value=current_value,
                absolute_delta=absolute_delta,
                percent_delta=percent_delta,
                contribution_pct=contribution_pct
            )
        
        return component_deltas
    
    def _identify_primary_driver(
        self,
        prior: MarginComponents,
        current: MarginComponents,
        component_deltas: Dict[str, DeltaComponent]
    ) -> Tuple[ChangeType, List[DeltaComponent]]:
        """Identify the primary driver of margin change."""
        
        # Sort components by absolute contribution
        sorted_components = sorted(
            component_deltas.values(),
            key=lambda x: abs(x.absolute_delta),
            reverse=True
        )
        
        # Get top contributors (Pareto principle - top 3 explain ≥80%)
        top_contributors = []
        cumulative_contribution = 0.0
        
        for component in sorted_components:
            if len(top_contributors) < 3 and abs(component.contribution_pct) > 5:
                top_contributors.append(component)
                cumulative_contribution += abs(component.contribution_pct)
                
                if cumulative_contribution >= self.significance_thresholds["pareto_threshold"]:
                    break
        
        # Determine primary driver type
        if not top_contributors:
            return ChangeType.VOLATILITY, []
        
        primary_component = top_contributors[0]
        
        # Check for position changes
        if prior.net_position != current.net_position:
            return ChangeType.POSITION_CHANGE, top_contributors
        
        # Check component-specific drivers
        if primary_component.component_name == "scan_risk":
            return ChangeType.SCAN_RISK, top_contributors
        elif primary_component.component_name == "inter_spread_charge":
            return ChangeType.SPREAD_CHARGE, top_contributors
        elif primary_component.component_name in ["short_opt_minimum", "long_opt_credit", "net_premium"]:
            return ChangeType.OPTION_PREMIUM, top_contributors
        else:
            return ChangeType.VOLATILITY, top_contributors
    
    def _generate_narrative(
        self,
        primary_driver: ChangeType,
        product: str,
        total_delta: Decimal,
        component_deltas: Dict[str, DeltaComponent],
        prior: Optional[MarginComponents],
        current: Optional[MarginComponents]
    ) -> str:
        """Generate plain-English narrative for the margin change."""
        
        templates = self.narrative_templates.get(primary_driver, [])
        if not templates:
            return f"Margin changed by ${total_delta:,.0f} for {product}."
        
        # Select template based on delta direction
        template_idx = 0 if total_delta >= 0 else min(1, len(templates) - 1)
        template = templates[template_idx]
        
        # Prepare template variables
        template_vars = {
            "product": product,
            "delta": abs(total_delta),
            "component_delta": 0,
            "position_change": 0
        }
        
        # Add component-specific variables
        if component_deltas:
            primary_component = max(component_deltas.values(), key=lambda x: abs(x.absolute_delta))
            template_vars["component_delta"] = abs(primary_component.absolute_delta)
        
        # Add position change information
        if prior and current:
            template_vars["position_change"] = current.net_position - prior.net_position
        
        try:
            return template.format(**template_vars)
        except KeyError as e:
            logger.warning(f"Template formatting error: {e}")
            return f"Margin changed by ${total_delta:,.0f} for {product}."
    
    def _is_significant_delta(self, delta: MarginDelta) -> bool:
        """Check if delta meets significance thresholds."""
        return (
            abs(delta.total_delta) >= self.significance_thresholds["absolute_min"] or
            abs(delta.total_delta_pct) >= self.significance_thresholds["percent_min"]
        )
    
    def generate_portfolio_summary(self, deltas: List[MarginDelta]) -> Dict[str, Any]:
        """Generate portfolio-level summary of margin changes."""
        
        if not deltas:
            return {
                "total_accounts": 0,
                "total_products": 0,
                "net_margin_change": 0,
                "largest_increase": None,
                "largest_decrease": None,
                "summary_narrative": "No significant margin changes detected."
            }
        
        # Calculate portfolio metrics
        accounts = set(d.account for d in deltas)
        products = set(d.product for d in deltas)
        net_change = sum(d.total_delta for d in deltas)
        
        # Find largest changes
        increases = [d for d in deltas if d.total_delta > 0]
        decreases = [d for d in deltas if d.total_delta < 0]
        
        largest_increase = max(increases, key=lambda x: x.total_delta) if increases else None
        largest_decrease = min(decreases, key=lambda x: x.total_delta) if decreases else None
        
        # Generate summary narrative
        if net_change > 1000:
            summary_narrative = f"Portfolio margin increased by ${net_change:,.0f} across {len(products)} products."
        elif net_change < -1000:
            summary_narrative = f"Portfolio margin decreased by ${abs(net_change):,.0f} across {len(products)} products."
        else:
            summary_narrative = f"Portfolio margin relatively stable with ${abs(net_change):,.0f} net change."
        
        return {
            "total_accounts": len(accounts),
            "total_products": len(products),
            "net_margin_change": float(net_change),
            "largest_increase": largest_increase.to_dict() if largest_increase else None,
            "largest_decrease": largest_decrease.to_dict() if largest_decrease else None,
            "summary_narrative": summary_narrative,
            "significant_changes": len(deltas)
        }
