"""Unit tests for assignment workflow and SLA management."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from app.exceptions.workflows.assignment_workflow import (
    AssignmentWorkflow,
    AssignmentStatus,
    SLASeverity,
    AssignmentRule,
    Team,
    AssignmentRuleConfig,
    ExceptionAssignment
)
from app.exceptions.clustering_analyzer import ExceptionCluster, ClusteringMethod
from app.models.recon import ReconException


class TestAssignmentWorkflow:
    """Test cases for assignment workflow and SLA management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.workflow = AssignmentWorkflow()
    
    def create_mock_exception(
        self, 
        trade_id: str, 
        symbol: str = "ES_FUT", 
        account: str = "BANK_001",
        difference_summary: str = "Price mismatch",
        internal_qty: float = 1000
    ) -> ReconException:
        """Create mock exception for testing."""
        exception = Mock(spec=ReconException)
        exception.trade_id = trade_id
        exception.symbol = symbol
        exception.account = account
        exception.difference_summary = difference_summary
        exception.internal_qty = internal_qty
        exception.external_qty = internal_qty
        return exception
    
    def create_mock_cluster(
        self,
        cluster_id: str,
        probable_cause: str = "price_mismatch",
        severity_level: str = "MEDIUM",
        exception_count: int = 5
    ) -> ExceptionCluster:
        """Create mock exception cluster for testing."""
        cluster = Mock(spec=ExceptionCluster)
        cluster.cluster_id = cluster_id
        cluster.probable_cause = probable_cause
        cluster.severity_level = severity_level
        cluster.exception_count = exception_count
        cluster.cluster_metadata = {"exception_ids": [f"TRADE_{i}" for i in range(exception_count)]}
        cluster.clustering_method = ClusteringMethod.EXACT_MATCH
        cluster.created_at = datetime.utcnow()
        cluster.updated_at = datetime.utcnow()
        return cluster
    
    def test_assign_individual_exceptions(self):
        """Test assignment of individual exceptions."""
        exceptions = [
            self.create_mock_exception("TRADE_001", difference_summary="Price mismatch"),
            self.create_mock_exception("TRADE_002", difference_summary="Quantity mismatch"),
            self.create_mock_exception("TRADE_003", difference_summary="System timeout")
        ]
        
        assignments = self.workflow.assign_exceptions(exceptions)
        
        assert len(assignments) == 3
        
        # Check assignment properties
        for assignment in assignments:
            assert assignment.assignment_id.startswith("EXC_")
            assert assignment.assigned_by == "system_auto_assignment"
            assert assignment.status == AssignmentStatus.ASSIGNED
            assert assignment.sla_due_at > datetime.utcnow()
            assert assignment.escalation_due_at is not None
            assert not assignment.is_sla_breached
            assert not assignment.is_escalated
    
    def test_assign_exception_clusters(self):
        """Test assignment of exception clusters."""
        clusters = [
            self.create_mock_cluster("CLUSTER_001", "price_mismatch", "HIGH"),
            self.create_mock_cluster("CLUSTER_002", "system_timeout", "CRITICAL"),
            self.create_mock_cluster("CLUSTER_003", "quantity_mismatch", "MEDIUM")
        ]
        
        assignments = self.workflow.assign_exceptions([], clusters)
        
        assert len(assignments) == 3
        
        # Check cluster assignment properties
        for assignment in assignments:
            assert assignment.assignment_id.startswith("CLUS_")
            assert assignment.cluster_id is not None
            assert assignment.assignment_confidence == 0.9  # High confidence for clusters
            assert assignment.sla_severity in [SLASeverity.HIGH, SLASeverity.CRITICAL, SLASeverity.MEDIUM]
    
    def test_team_assignment_by_cause(self):
        """Test team assignment based on probable cause."""
        # Test different causes map to correct teams
        price_cluster = self.create_mock_cluster("C1", "price_mismatch")
        tech_cluster = self.create_mock_cluster("C2", "system_timeout")
        ops_cluster = self.create_mock_cluster("C3", "quantity_mismatch")
        
        clusters = [price_cluster, tech_cluster, ops_cluster]
        assignments = self.workflow.assign_exceptions([], clusters)
        
        # Check team assignments
        team_assignments = {a.cluster_id: a.assigned_team_id for a in assignments}
        
        assert team_assignments["C1"] == "TRADING_TEAM_001"  # Price issues to trading
        assert team_assignments["C2"] == "TECH_TEAM_001"     # Tech issues to tech team
        assert team_assignments["C3"] == "OPS_TEAM_001"      # Ops issues to ops team
    
    def test_sla_severity_determination(self):
        """Test SLA severity determination based on exception value."""
        # High value exception should get critical SLA
        high_value_exception = self.create_mock_exception("T1", internal_qty=50000000)  # 50M
        medium_value_exception = self.create_mock_exception("T2", internal_qty=500000)   # 500K
        low_value_exception = self.create_mock_exception("T3", internal_qty=10000)       # 10K
        
        exceptions = [high_value_exception, medium_value_exception, low_value_exception]
        assignments = self.workflow.assign_exceptions(exceptions)
        
        # Check SLA severity assignments
        severity_map = {a.exception_id: a.sla_severity for a in assignments}
        
        assert severity_map["T1"] == SLASeverity.CRITICAL
        assert severity_map["T2"] == SLASeverity.MEDIUM
        assert severity_map["T3"] == SLASeverity.LOW
    
    def test_sla_due_date_calculation(self):
        """Test SLA due date calculation based on severity."""
        now = datetime.utcnow()
        
        # Test different severity levels
        critical_due = self.workflow._calculate_sla_due_date("CRITICAL")
        high_due = self.workflow._calculate_sla_due_date("HIGH")
        medium_due = self.workflow._calculate_sla_due_date("MEDIUM")
        low_due = self.workflow._calculate_sla_due_date("LOW")
        
        # Check time differences
        critical_hours = (critical_due - now).total_seconds() / 3600
        high_hours = (high_due - now).total_seconds() / 3600
        medium_hours = (medium_due - now).total_seconds() / 3600
        low_hours = (low_due - now).total_seconds() / 3600
        
        # Verify SLA hours are correct
        assert abs(critical_hours - 2) < 0.1   # 2 hours
        assert abs(high_hours - 8) < 0.1       # 8 hours
        assert abs(medium_hours - 24) < 0.1    # 24 hours
        assert abs(low_hours - 72) < 0.1       # 72 hours
    
    def test_escalation_date_calculation(self):
        """Test escalation date calculation (50% of SLA time)."""
        now = datetime.utcnow()
        
        escalation_due = self.workflow._calculate_escalation_date("MEDIUM")
        sla_due = self.workflow._calculate_sla_due_date("MEDIUM")
        
        # Escalation should be at 50% of SLA time
        expected_escalation = now + (sla_due - now) * 0.5
        
        # Allow small time difference for test execution
        time_diff = abs((escalation_due - expected_escalation).total_seconds())
        assert time_diff < 1  # Less than 1 second difference
    
    def test_assignment_status_update(self):
        """Test assignment status updates."""
        exception = self.create_mock_exception("TRADE_001")
        assignments = self.workflow.assign_exceptions([exception])
        assignment = assignments[0]
        
        # Test status update to IN_PROGRESS
        success = self.workflow.update_assignment_status(
            assignment.assignment_id,
            AssignmentStatus.IN_PROGRESS,
            "user_001",
            "Started working on this"
        )
        
        assert success
        assert assignment.status == AssignmentStatus.IN_PROGRESS
        assert assignment.status_updated_at is not None
    
    def test_assignment_resolution(self):
        """Test assignment resolution with SLA tracking."""
        exception = self.create_mock_exception("TRADE_001")
        assignments = self.workflow.assign_exceptions([exception])
        assignment = assignments[0]
        
        # Resolve assignment
        success = self.workflow.update_assignment_status(
            assignment.assignment_id,
            AssignmentStatus.RESOLVED,
            "user_001",
            "Issue resolved successfully"
        )
        
        assert success
        assert assignment.status == AssignmentStatus.RESOLVED
        assert assignment.resolved_at is not None
        assert assignment.resolved_by == "user_001"
        assert assignment.resolution_notes == "Issue resolved successfully"
        
        # Check SLA breach status (should not be breached if resolved quickly)
        assert not assignment.is_sla_breached
    
    def test_assignment_escalation(self):
        """Test assignment escalation workflow."""
        exception = self.create_mock_exception("TRADE_001")
        assignments = self.workflow.assign_exceptions([exception])
        assignment = assignments[0]
        
        original_team = assignment.assigned_team_id
        
        # Escalate assignment
        success = self.workflow.update_assignment_status(
            assignment.assignment_id,
            AssignmentStatus.ESCALATED,
            "system_auto_escalation"
        )
        
        assert success
        assert assignment.status == AssignmentStatus.ESCALATED
        assert assignment.is_escalated
        
        # Should be reassigned to escalation team
        team = self.workflow.teams.get(original_team)
        if team and team.escalation_team_id:
            assert assignment.assigned_team_id == team.escalation_team_id
    
    def test_sla_breach_detection(self):
        """Test SLA breach detection and tracking."""
        exception = self.create_mock_exception("TRADE_001")
        assignments = self.workflow.assign_exceptions([exception])
        assignment = assignments[0]
        
        # Simulate SLA breach by setting due date in the past
        assignment.sla_due_at = datetime.utcnow() - timedelta(hours=1)
        
        # Check for SLA breaches
        breached_assignments = self.workflow.check_sla_breaches()
        
        assert len(breached_assignments) == 1
        assert breached_assignments[0].assignment_id == assignment.assignment_id
        assert assignment.is_sla_breached
    
    def test_auto_escalation_on_time_breach(self):
        """Test automatic escalation when escalation time is reached."""
        exception = self.create_mock_exception("TRADE_001")
        assignments = self.workflow.assign_exceptions([exception])
        assignment = assignments[0]
        
        # Simulate escalation time breach
        assignment.escalation_due_at = datetime.utcnow() - timedelta(minutes=30)
        
        # Check for SLA breaches (should trigger auto-escalation)
        breached_assignments = self.workflow.check_sla_breaches()
        
        assert len(breached_assignments) == 1
        assert assignment.status == AssignmentStatus.ESCALATED
        assert assignment.is_escalated
    
    def test_team_workload_calculation(self):
        """Test team workload statistics calculation."""
        # Create multiple assignments for a team
        exceptions = [
            self.create_mock_exception(f"TRADE_{i}") for i in range(5)
        ]
        assignments = self.workflow.assign_exceptions(exceptions)
        
        # All should be assigned to OPS_TEAM_001 by default
        team_id = "OPS_TEAM_001"
        workload = self.workflow.get_team_workload(team_id)
        
        assert workload["team_id"] == team_id
        assert workload["current_workload"] == 5
        assert workload["utilization_pct"] > 0
        assert "status_breakdown" in workload
        assert "sla_metrics" in workload
        
        # Check status breakdown
        status_breakdown = workload["status_breakdown"]
        assert status_breakdown[AssignmentStatus.ASSIGNED.value] == 5
    
    def test_assignment_rule_matching(self):
        """Test assignment rule matching logic."""
        # Test price mismatch rule
        price_exception = self.create_mock_exception("T1", difference_summary="Price mismatch detected")
        matching_rule = self.workflow._find_matching_rule(price_exception)
        
        if matching_rule:
            assert matching_rule.rule_id == "PRICE_BREAKS_TO_TRADING"
            assert matching_rule.target_team_id == "TRADING_TEAM_001"
        
        # Test system timeout rule
        timeout_exception = self.create_mock_exception("T2", difference_summary="System timeout occurred")
        matching_rule = self.workflow._find_matching_rule(timeout_exception)
        
        if matching_rule:
            assert matching_rule.rule_id == "SYSTEM_ISSUES_TO_TECH"
            assert matching_rule.target_team_id == "TECH_TEAM_001"
    
    def test_large_amount_escalation_rule(self):
        """Test large amount escalation to management."""
        # Create high-value exception
        large_exception = self.create_mock_exception("T1", internal_qty=100000000)  # 100M
        
        matching_rule = self.workflow._find_matching_rule(large_exception)
        
        if matching_rule:
            assert matching_rule.rule_id == "LARGE_AMOUNTS_TO_MANAGEMENT"
            assert matching_rule.target_team_id == "MANAGER_TEAM_001"
    
    def test_cause_code_extraction(self):
        """Test cause code extraction for assignment rules."""
        price_exception = self.create_mock_exception("T1", difference_summary="Price mismatch: 100 vs 101")
        assert self.workflow._extract_cause_code(price_exception) == "price_mismatch"
        
        qty_exception = self.create_mock_exception("T2", difference_summary="Quantity difference found")
        assert self.workflow._extract_cause_code(qty_exception) == "quantity_mismatch"
        
        timeout_exception = self.create_mock_exception("T3", difference_summary="System timeout error")
        assert self.workflow._extract_cause_code(timeout_exception) == "system_timeout"
    
    def test_product_type_extraction(self):
        """Test product type extraction for assignment rules."""
        assert self.workflow._extract_product_type("ES_MAR24_FUT") == "equity_futures"
        assert self.workflow._extract_product_type("NQ_JUN24_FUT") == "equity_futures"
        assert self.workflow._extract_product_type("IRS_5Y_USD") == "interest_rate_swap"
        assert self.workflow._extract_product_type("FX_FWD_EURUSD") == "fx_forward"
        assert self.workflow._extract_product_type("UNKNOWN_PRODUCT") == "other"
    
    def test_default_team_configuration(self):
        """Test default team configuration."""
        # Check that default teams are configured
        assert "OPS_TEAM_001" in self.workflow.teams
        assert "TRADING_TEAM_001" in self.workflow.teams
        assert "TECH_TEAM_001" in self.workflow.teams
        assert "MANAGER_TEAM_001" in self.workflow.teams
        
        # Check team properties
        ops_team = self.workflow.teams["OPS_TEAM_001"]
        assert ops_team.team_name == "Operations Team"
        assert ops_team.team_type == "operations"
        assert ops_team.capacity > 0
        assert ops_team.escalation_team_id == "MANAGER_TEAM_001"
    
    def test_assignment_confidence_scoring(self):
        """Test assignment confidence scoring."""
        # Cluster assignments should have high confidence
        cluster = self.create_mock_cluster("C1", "price_mismatch")
        cluster_assignments = self.workflow.assign_exceptions([], [cluster])
        
        assert cluster_assignments[0].assignment_confidence == 0.9
        
        # Rule-based individual assignments should have medium confidence
        price_exception = self.create_mock_exception("T1", difference_summary="Price mismatch")
        individual_assignments = self.workflow.assign_exceptions([price_exception])
        
        # Confidence depends on rule matching
        assignment = individual_assignments[0]
        assert 0.5 <= assignment.assignment_confidence <= 1.0
    
    def test_mixed_exception_and_cluster_assignment(self):
        """Test assignment of both individual exceptions and clusters."""
        # Create individual exceptions
        individual_exceptions = [
            self.create_mock_exception("INDIVIDUAL_001"),
            self.create_mock_exception("INDIVIDUAL_002")
        ]
        
        # Create clusters
        clusters = [
            self.create_mock_cluster("CLUSTER_001", exception_count=3)
        ]
        
        assignments = self.workflow.assign_exceptions(individual_exceptions, clusters)
        
        # Should have assignments for both individual exceptions and cluster
        assert len(assignments) == 3  # 2 individual + 1 cluster
        
        # Check assignment types
        cluster_assignments = [a for a in assignments if a.cluster_id is not None]
        individual_assignments = [a for a in assignments if a.cluster_id is None]
        
        assert len(cluster_assignments) == 1
        assert len(individual_assignments) == 2
    
    @pytest.mark.parametrize("severity,expected_hours", [
        ("CRITICAL", 2),
        ("HIGH", 8),
        ("MEDIUM", 24),
        ("LOW", 72)
    ])
    def test_sla_hours_by_severity(self, severity, expected_hours):
        """Test SLA hours calculation for different severity levels."""
        now = datetime.utcnow()
        due_date = self.workflow._calculate_sla_due_date(severity)
        
        actual_hours = (due_date - now).total_seconds() / 3600
        assert abs(actual_hours - expected_hours) < 0.1
