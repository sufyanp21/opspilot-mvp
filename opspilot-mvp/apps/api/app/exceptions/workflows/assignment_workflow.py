"""Assignment workflow for automatic exception routing and SLA management."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.exceptions.clustering_analyzer import ExceptionCluster
from app.models.recon import ReconException

logger = logging.getLogger(__name__)


class AssignmentRule(Enum):
    """Types of assignment rules."""
    CAUSE_CODE = "cause_code"
    PRODUCT_TYPE = "product_type"
    COUNTERPARTY = "counterparty"
    SEVERITY = "severity"
    AMOUNT_THRESHOLD = "amount_threshold"
    GEOGRAPHIC = "geographic"


class SLASeverity(Enum):
    """SLA severity levels with time limits."""
    CRITICAL = "CRITICAL"  # 2 hours
    HIGH = "HIGH"         # 8 hours
    MEDIUM = "MEDIUM"     # 24 hours
    LOW = "LOW"           # 72 hours


class AssignmentStatus(Enum):
    """Assignment status values."""
    UNASSIGNED = "UNASSIGNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


@dataclass
class Team:
    """Represents a team that can be assigned exceptions."""
    team_id: str
    team_name: str
    team_type: str  # e.g., "operations", "trading", "technology"
    specializations: List[str]
    capacity: int
    current_workload: int
    escalation_team_id: Optional[str] = None
    
    # Contact information
    email: Optional[str] = None
    slack_channel: Optional[str] = None
    
    # Working hours and timezone
    timezone: str = "UTC"
    working_hours_start: int = 9  # 24-hour format
    working_hours_end: int = 17


@dataclass
class AssignmentRuleConfig:
    """Configuration for assignment rules."""
    rule_id: str
    rule_type: AssignmentRule
    priority: int  # Lower number = higher priority
    conditions: Dict[str, Any]
    target_team_id: str
    is_active: bool = True
    
    # SLA configuration
    sla_hours: Optional[int] = None
    escalation_hours: Optional[int] = None


@dataclass
class SLAPolicy:
    """SLA policy configuration."""
    severity: SLASeverity
    response_time_hours: int
    resolution_time_hours: int
    escalation_time_hours: int
    business_hours_only: bool = True
    
    # Notification settings
    notify_at_50_percent: bool = True
    notify_at_80_percent: bool = True
    notify_on_breach: bool = True


@dataclass
class ExceptionAssignment:
    """Represents an exception assignment."""
    assignment_id: str
    exception_id: str
    cluster_id: Optional[str]
    assigned_team_id: str
    assigned_by: str
    assigned_at: datetime
    
    # SLA tracking
    sla_severity: SLASeverity
    sla_due_at: datetime
    escalation_due_at: Optional[datetime]
    is_sla_breached: bool = False
    is_escalated: bool = False
    
    # Status tracking
    status: AssignmentStatus = AssignmentStatus.ASSIGNED
    status_updated_at: datetime = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    # Assignment metadata
    assignment_reason: str = ""
    assignment_confidence: float = 1.0
    manual_override: bool = False


class AssignmentWorkflow:
    """Manages automatic assignment of exceptions to teams with SLA tracking."""
    
    def __init__(self):
        self.teams: Dict[str, Team] = {}
        self.assignment_rules: List[AssignmentRuleConfig] = []
        self.sla_policies: Dict[SLASeverity, SLAPolicy] = {}
        self.assignments: Dict[str, ExceptionAssignment] = {}
        
        # Initialize default configuration
        self._initialize_default_config()
    
    def assign_exceptions(
        self, 
        exceptions: List[ReconException], 
        clusters: Optional[List[ExceptionCluster]] = None
    ) -> List[ExceptionAssignment]:
        """
        Assign exceptions to teams based on rules and create SLA tracking.
        
        Args:
            exceptions: List of exceptions to assign
            clusters: Optional list of exception clusters
            
        Returns:
            List of created assignments
        """
        try:
            logger.info(f"Assigning {len(exceptions)} exceptions to teams")
            
            assignments = []
            
            # Create cluster-based assignments first
            if clusters:
                cluster_assignments = self._assign_clusters(clusters)
                assignments.extend(cluster_assignments)
                
                # Track which exceptions are already assigned via clusters
                clustered_exception_ids = set()
                for cluster in clusters:
                    clustered_exception_ids.update(
                        cluster.cluster_metadata.get("exception_ids", [])
                    )
            else:
                clustered_exception_ids = set()
            
            # Assign individual exceptions not in clusters
            individual_exceptions = [
                exc for exc in exceptions 
                if exc.trade_id not in clustered_exception_ids
            ]
            
            for exception in individual_exceptions:
                assignment = self._assign_individual_exception(exception)
                if assignment:
                    assignments.append(assignment)
            
            # Store assignments
            for assignment in assignments:
                self.assignments[assignment.assignment_id] = assignment
            
            logger.info(f"Created {len(assignments)} exception assignments")
            return assignments
            
        except Exception as e:
            logger.error(f"Error in exception assignment workflow: {e}")
            raise
    
    def update_assignment_status(
        self, 
        assignment_id: str, 
        new_status: AssignmentStatus, 
        updated_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """Update assignment status and handle SLA implications."""
        try:
            assignment = self.assignments.get(assignment_id)
            if not assignment:
                logger.warning(f"Assignment {assignment_id} not found")
                return False
            
            old_status = assignment.status
            assignment.status = new_status
            assignment.status_updated_at = datetime.utcnow()
            
            # Handle status-specific logic
            if new_status == AssignmentStatus.RESOLVED:
                assignment.resolved_at = datetime.utcnow()
                assignment.resolved_by = updated_by
                assignment.resolution_notes = notes
                
                # Check if SLA was met
                if assignment.resolved_at > assignment.sla_due_at:
                    assignment.is_sla_breached = True
                    logger.warning(f"Assignment {assignment_id} resolved after SLA breach")
            
            elif new_status == AssignmentStatus.ESCALATED:
                assignment.is_escalated = True
                # Reassign to escalation team if configured
                team = self.teams.get(assignment.assigned_team_id)
                if team and team.escalation_team_id:
                    assignment.assigned_team_id = team.escalation_team_id
                    assignment.assignment_reason += " [ESCALATED]"
            
            logger.info(f"Assignment {assignment_id} status updated: {old_status} -> {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating assignment status: {e}")
            return False
    
    def check_sla_breaches(self) -> List[ExceptionAssignment]:
        """Check for SLA breaches and return assignments requiring attention."""
        try:
            now = datetime.utcnow()
            breached_assignments = []
            
            for assignment in self.assignments.values():
                if assignment.status in [AssignmentStatus.RESOLVED, AssignmentStatus.CLOSED]:
                    continue
                
                # Check for SLA breach
                if now > assignment.sla_due_at and not assignment.is_sla_breached:
                    assignment.is_sla_breached = True
                    breached_assignments.append(assignment)
                    logger.warning(f"SLA breach detected for assignment {assignment.assignment_id}")
                
                # Check for escalation due
                if (assignment.escalation_due_at and 
                    now > assignment.escalation_due_at and 
                    not assignment.is_escalated):
                    
                    self.update_assignment_status(
                        assignment.assignment_id, 
                        AssignmentStatus.ESCALATED,
                        "system_auto_escalation"
                    )
                    breached_assignments.append(assignment)
            
            return breached_assignments
            
        except Exception as e:
            logger.error(f"Error checking SLA breaches: {e}")
            return []
    
    def get_team_workload(self, team_id: str) -> Dict[str, Any]:
        """Get current workload statistics for a team."""
        try:
            team = self.teams.get(team_id)
            if not team:
                return {}
            
            # Count assignments by status
            team_assignments = [
                a for a in self.assignments.values() 
                if a.assigned_team_id == team_id
            ]
            
            status_counts = {}
            for status in AssignmentStatus:
                status_counts[status.value] = len([
                    a for a in team_assignments if a.status == status
                ])
            
            # Calculate SLA metrics
            active_assignments = [
                a for a in team_assignments 
                if a.status not in [AssignmentStatus.RESOLVED, AssignmentStatus.CLOSED]
            ]
            
            sla_breached = len([a for a in active_assignments if a.is_sla_breached])
            escalated = len([a for a in active_assignments if a.is_escalated])
            
            return {
                "team_id": team_id,
                "team_name": team.team_name,
                "capacity": team.capacity,
                "current_workload": len(active_assignments),
                "utilization_pct": (len(active_assignments) / team.capacity * 100) if team.capacity > 0 else 0,
                "status_breakdown": status_counts,
                "sla_metrics": {
                    "active_assignments": len(active_assignments),
                    "sla_breached": sla_breached,
                    "escalated": escalated,
                    "breach_rate_pct": (sla_breached / len(active_assignments) * 100) if active_assignments else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting team workload: {e}")
            return {}
    
    def _assign_clusters(self, clusters: List[ExceptionCluster]) -> List[ExceptionAssignment]:
        """Assign exception clusters to teams."""
        assignments = []
        
        for cluster in clusters:
            team_id = self._find_best_team_for_cluster(cluster)
            if not team_id:
                logger.warning(f"No suitable team found for cluster {cluster.cluster_id}")
                continue
            
            assignment = ExceptionAssignment(
                assignment_id=f"CLUS_{cluster.cluster_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                exception_id=cluster.cluster_id,
                cluster_id=cluster.cluster_id,
                assigned_team_id=team_id,
                assigned_by="system_auto_assignment",
                assigned_at=datetime.utcnow(),
                sla_severity=self._map_severity_to_sla(cluster.severity_level),
                sla_due_at=self._calculate_sla_due_date(cluster.severity_level),
                escalation_due_at=self._calculate_escalation_date(cluster.severity_level),
                assignment_reason=f"Cluster assignment: {cluster.probable_cause}",
                assignment_confidence=0.9  # High confidence for cluster assignments
            )
            
            assignments.append(assignment)
        
        return assignments
    
    def _assign_individual_exception(self, exception: ReconException) -> Optional[ExceptionAssignment]:
        """Assign individual exception to team based on rules."""
        # Find matching assignment rule
        matching_rule = self._find_matching_rule(exception)
        if not matching_rule:
            # Default assignment to operations team
            team_id = "OPS_TEAM_001"
            assignment_reason = "Default assignment - no specific rule matched"
            confidence = 0.5
        else:
            team_id = matching_rule.target_team_id
            assignment_reason = f"Rule-based assignment: {matching_rule.rule_id}"
            confidence = 0.8
        
        # Determine severity
        severity = self._determine_exception_severity(exception)
        
        assignment = ExceptionAssignment(
            assignment_id=f"EXC_{exception.trade_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            exception_id=exception.trade_id,
            cluster_id=None,
            assigned_team_id=team_id,
            assigned_by="system_auto_assignment",
            assigned_at=datetime.utcnow(),
            sla_severity=severity,
            sla_due_at=self._calculate_sla_due_date(severity.value),
            escalation_due_at=self._calculate_escalation_date(severity.value),
            assignment_reason=assignment_reason,
            assignment_confidence=confidence
        )
        
        return assignment
    
    def _find_best_team_for_cluster(self, cluster: ExceptionCluster) -> Optional[str]:
        """Find best team for exception cluster based on specialization and workload."""
        # Simple team selection based on probable cause
        cause_team_mapping = {
            "price_mismatch": "TRADING_TEAM_001",
            "quantity_mismatch": "OPS_TEAM_001", 
            "date_mismatch": "OPS_TEAM_001",
            "missing_trade": "TRADING_TEAM_001",
            "system_timeout": "TECH_TEAM_001",
            "data_format": "TECH_TEAM_001"
        }
        
        return cause_team_mapping.get(cluster.probable_cause, "OPS_TEAM_001")
    
    def _find_matching_rule(self, exception: ReconException) -> Optional[AssignmentRuleConfig]:
        """Find matching assignment rule for exception."""
        # Sort rules by priority
        sorted_rules = sorted(self.assignment_rules, key=lambda r: r.priority)
        
        for rule in sorted_rules:
            if not rule.is_active:
                continue
            
            if self._rule_matches_exception(rule, exception):
                return rule
        
        return None
    
    def _rule_matches_exception(self, rule: AssignmentRuleConfig, exception: ReconException) -> bool:
        """Check if assignment rule matches exception."""
        if rule.rule_type == AssignmentRule.CAUSE_CODE:
            cause = self._extract_cause_code(exception)
            return cause in rule.conditions.get("causes", [])
        
        elif rule.rule_type == AssignmentRule.PRODUCT_TYPE:
            product_type = self._extract_product_type(exception.symbol)
            return product_type in rule.conditions.get("product_types", [])
        
        elif rule.rule_type == AssignmentRule.COUNTERPARTY:
            return exception.account in rule.conditions.get("counterparties", [])
        
        elif rule.rule_type == AssignmentRule.AMOUNT_THRESHOLD:
            amount = getattr(exception, 'internal_qty', 0) or 0
            min_amount = rule.conditions.get("min_amount", 0)
            max_amount = rule.conditions.get("max_amount", float('inf'))
            return min_amount <= amount <= max_amount
        
        return False
    
    def _determine_exception_severity(self, exception: ReconException) -> SLASeverity:
        """Determine SLA severity for exception."""
        # Simple severity determination logic
        if hasattr(exception, 'internal_qty') and exception.internal_qty:
            amount = abs(exception.internal_qty)
            if amount > 10000000:  # > 10M
                return SLASeverity.CRITICAL
            elif amount > 1000000:  # > 1M
                return SLASeverity.HIGH
            elif amount > 100000:   # > 100K
                return SLASeverity.MEDIUM
        
        return SLASeverity.LOW
    
    def _map_severity_to_sla(self, severity_str: str) -> SLASeverity:
        """Map string severity to SLA severity enum."""
        mapping = {
            "CRITICAL": SLASeverity.CRITICAL,
            "HIGH": SLASeverity.HIGH,
            "MEDIUM": SLASeverity.MEDIUM,
            "LOW": SLASeverity.LOW
        }
        return mapping.get(severity_str, SLASeverity.MEDIUM)
    
    def _calculate_sla_due_date(self, severity: str) -> datetime:
        """Calculate SLA due date based on severity."""
        now = datetime.utcnow()
        
        # SLA hours by severity
        sla_hours = {
            "CRITICAL": 2,
            "HIGH": 8,
            "MEDIUM": 24,
            "LOW": 72
        }
        
        hours = sla_hours.get(severity, 24)
        return now + timedelta(hours=hours)
    
    def _calculate_escalation_date(self, severity: str) -> Optional[datetime]:
        """Calculate escalation due date (typically 50% of SLA time)."""
        sla_due = self._calculate_sla_due_date(severity)
        now = datetime.utcnow()
        
        # Escalate at 50% of SLA time
        escalation_time = now + (sla_due - now) * 0.5
        return escalation_time
    
    def _extract_cause_code(self, exception: ReconException) -> str:
        """Extract cause code from exception (reuse from clustering analyzer)."""
        if not exception.difference_summary:
            return "unknown"
        
        summary = exception.difference_summary.lower()
        
        if "price" in summary or "rate" in summary:
            return "price_mismatch"
        elif "quantity" in summary or "notional" in summary:
            return "quantity_mismatch"
        elif "date" in summary:
            return "date_mismatch"
        elif "missing" in summary:
            return "missing_trade"
        elif "timeout" in summary:
            return "system_timeout"
        
        return "other"
    
    def _extract_product_type(self, symbol: str) -> str:
        """Extract product type from symbol."""
        if not symbol:
            return "unknown"
        
        symbol = symbol.upper()
        
        if any(fut in symbol for fut in ["ES", "NQ"]):
            return "equity_futures"
        elif "IRS" in symbol:
            return "interest_rate_swap"
        elif "FX" in symbol:
            return "fx_forward"
        
        return "other"
    
    def _initialize_default_config(self):
        """Initialize default teams, rules, and SLA policies."""
        # Default teams
        self.teams = {
            "OPS_TEAM_001": Team(
                team_id="OPS_TEAM_001",
                team_name="Operations Team",
                team_type="operations",
                specializations=["trade_settlement", "reconciliation", "general"],
                capacity=20,
                current_workload=0,
                escalation_team_id="MANAGER_TEAM_001"
            ),
            "TRADING_TEAM_001": Team(
                team_id="TRADING_TEAM_001", 
                team_name="Trading Desk",
                team_type="trading",
                specializations=["price_validation", "market_data", "trade_booking"],
                capacity=10,
                current_workload=0,
                escalation_team_id="MANAGER_TEAM_001"
            ),
            "TECH_TEAM_001": Team(
                team_id="TECH_TEAM_001",
                team_name="Technology Team", 
                team_type="technology",
                specializations=["system_issues", "data_format", "connectivity"],
                capacity=15,
                current_workload=0,
                escalation_team_id="MANAGER_TEAM_001"
            ),
            "MANAGER_TEAM_001": Team(
                team_id="MANAGER_TEAM_001",
                team_name="Management Team",
                team_type="management", 
                specializations=["escalation", "oversight"],
                capacity=5,
                current_workload=0
            )
        }
        
        # Default assignment rules
        self.assignment_rules = [
            AssignmentRuleConfig(
                rule_id="PRICE_BREAKS_TO_TRADING",
                rule_type=AssignmentRule.CAUSE_CODE,
                priority=1,
                conditions={"causes": ["price_mismatch"]},
                target_team_id="TRADING_TEAM_001"
            ),
            AssignmentRuleConfig(
                rule_id="SYSTEM_ISSUES_TO_TECH", 
                rule_type=AssignmentRule.CAUSE_CODE,
                priority=2,
                conditions={"causes": ["system_timeout", "data_format"]},
                target_team_id="TECH_TEAM_001"
            ),
            AssignmentRuleConfig(
                rule_id="LARGE_AMOUNTS_TO_MANAGEMENT",
                rule_type=AssignmentRule.AMOUNT_THRESHOLD,
                priority=3,
                conditions={"min_amount": 50000000},  # > 50M
                target_team_id="MANAGER_TEAM_001"
            )
        ]
        
        # Default SLA policies
        self.sla_policies = {
            SLASeverity.CRITICAL: SLAPolicy(
                severity=SLASeverity.CRITICAL,
                response_time_hours=1,
                resolution_time_hours=2,
                escalation_time_hours=1
            ),
            SLASeverity.HIGH: SLAPolicy(
                severity=SLASeverity.HIGH,
                response_time_hours=2,
                resolution_time_hours=8,
                escalation_time_hours=4
            ),
            SLASeverity.MEDIUM: SLAPolicy(
                severity=SLASeverity.MEDIUM,
                response_time_hours=4,
                resolution_time_hours=24,
                escalation_time_hours=12
            ),
            SLASeverity.LOW: SLAPolicy(
                severity=SLASeverity.LOW,
                response_time_hours=8,
                resolution_time_hours=72,
                escalation_time_hours=36
            )
        }
