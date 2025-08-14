"""API endpoints for exception grouping and SLA workflow management."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from datetime import datetime
import logging

from app.exceptions.clustering_analyzer import ExceptionClusteringAnalyzer, ExceptionCluster, ClusteringConfig
from app.exceptions.workflows.assignment_workflow import AssignmentWorkflow, AssignmentStatus, SLASeverity
from app.models.recon import ReconException
from app.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/exceptions", tags=["exceptions"])


# Pydantic models for API
class ClusteringConfigRequest(BaseModel):
    """Request model for clustering configuration."""
    enable_exact_matching: bool = True
    enable_fuzzy_matching: bool = True
    fuzzy_similarity_threshold: float = 0.8
    min_cluster_size: int = 2
    max_clusters_per_run: int = 100


class ExceptionClusterResponse(BaseModel):
    """Response model for exception cluster."""
    cluster_id: str
    cluster_key: str
    clustering_method: str
    exception_count: int
    probable_cause: str
    severity_level: str
    created_at: datetime
    accounts_affected: List[str]
    products_affected: List[str]
    exception_types: List[str]
    representative_exception_id: str
    cluster_metadata: Dict[str, Any]


class AssignmentRequest(BaseModel):
    """Request model for manual assignment."""
    exception_ids: List[str]
    team_id: str
    assigned_by: str
    notes: Optional[str] = None
    override_sla: Optional[str] = None


class AssignmentStatusUpdate(BaseModel):
    """Request model for assignment status update."""
    assignment_id: str
    new_status: str
    updated_by: str
    notes: Optional[str] = None


class BulkActionRequest(BaseModel):
    """Request model for bulk actions on exceptions."""
    exception_ids: List[str]
    action: str  # "assign", "resolve", "escalate", "close"
    team_id: Optional[str] = None
    assigned_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class SLABreachResponse(BaseModel):
    """Response model for SLA breach information."""
    assignment_id: str
    exception_id: str
    cluster_id: Optional[str]
    assigned_team_id: str
    sla_severity: str
    sla_due_at: datetime
    hours_overdue: float
    is_escalated: bool
    assignment_reason: str


class TeamWorkloadResponse(BaseModel):
    """Response model for team workload statistics."""
    team_id: str
    team_name: str
    capacity: int
    current_workload: int
    utilization_pct: float
    status_breakdown: Dict[str, int]
    sla_metrics: Dict[str, Any]


# Global instances (in production, these would be dependency-injected)
clustering_analyzer = ExceptionClusteringAnalyzer()
assignment_workflow = AssignmentWorkflow()


@router.post("/cluster", response_model=List[ExceptionClusterResponse])
async def cluster_exceptions(
    run_id: Optional[str] = None,
    config: Optional[ClusteringConfigRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Cluster exceptions for analysis and grouping.
    
    Args:
        run_id: Optional reconciliation run ID to cluster exceptions from
        config: Clustering configuration parameters
        db: Database session
        
    Returns:
        List of exception clusters
    """
    try:
        # Get exceptions to cluster
        query = db.query(ReconException)
        if run_id:
            query = query.filter(ReconException.run_id == run_id)
        
        # Only cluster open exceptions
        exceptions = query.filter(ReconException.status == "OPEN").all()
        
        if not exceptions:
            return []
        
        # Configure clustering analyzer
        if config:
            clustering_config = ClusteringConfig(
                enable_exact_matching=config.enable_exact_matching,
                enable_fuzzy_matching=config.enable_fuzzy_matching,
                fuzzy_similarity_threshold=config.fuzzy_similarity_threshold,
                min_cluster_size=config.min_cluster_size,
                max_clusters_per_run=config.max_clusters_per_run
            )
            clustering_analyzer.config = clustering_config
        
        # Perform clustering analysis
        clusters = clustering_analyzer.analyze_exceptions(exceptions)
        
        # Convert to response format
        cluster_responses = []
        for cluster in clusters:
            cluster_response = ExceptionClusterResponse(
                cluster_id=cluster.cluster_id,
                cluster_key=cluster.cluster_key,
                clustering_method=cluster.clustering_method.value,
                exception_count=cluster.exception_count,
                probable_cause=cluster.probable_cause,
                severity_level=cluster.severity_level,
                created_at=cluster.created_at,
                accounts_affected=list(cluster.accounts_affected),
                products_affected=list(cluster.products_affected),
                exception_types=list(cluster.exception_types),
                representative_exception_id=cluster.representative_exception.id if hasattr(cluster.representative_exception, 'id') else "",
                cluster_metadata=cluster.cluster_metadata
            )
            cluster_responses.append(cluster_response)
        
        logger.info(f"Clustered {len(exceptions)} exceptions into {len(clusters)} clusters")
        return cluster_responses
        
    except Exception as e:
        logger.error(f"Error clustering exceptions: {e}")
        raise HTTPException(status_code=500, detail=f"Error clustering exceptions: {str(e)}")


@router.post("/assign")
async def assign_exceptions(
    request: AssignmentRequest,
    db: Session = Depends(get_db)
):
    """
    Manually assign exceptions to a team.
    
    Args:
        request: Assignment request with exception IDs and team information
        db: Database session
        
    Returns:
        Assignment confirmation
    """
    try:
        # Get exceptions to assign
        exceptions = db.query(ReconException).filter(
            ReconException.id.in_(request.exception_ids)
        ).all()
        
        if not exceptions:
            raise HTTPException(status_code=404, detail="No exceptions found with provided IDs")
        
        # Create assignments using workflow
        assignments = assignment_workflow.assign_exceptions(exceptions)
        
        # Update database records
        for exception in exceptions:
            exception.assigned_to = request.assigned_by
            exception.assigned_at = datetime.utcnow()
            exception.assigned_team_id = request.team_id
            exception.assignment_status = AssignmentStatus.ASSIGNED.value
            exception.assignment_reason = f"Manual assignment: {request.notes or 'No notes provided'}"
            exception.manual_override = True
            
            # Set SLA if overridden
            if request.override_sla:
                exception.sla_severity = request.override_sla
        
        db.commit()
        
        logger.info(f"Assigned {len(exceptions)} exceptions to team {request.team_id}")
        return {
            "status": "success",
            "message": f"Assigned {len(exceptions)} exceptions to team {request.team_id}",
            "assigned_count": len(exceptions),
            "assignments": [a.assignment_id for a in assignments]
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning exceptions: {e}")
        raise HTTPException(status_code=500, detail=f"Error assigning exceptions: {str(e)}")


@router.put("/assignment/status")
async def update_assignment_status(
    request: AssignmentStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update assignment status for exception workflow.
    
    Args:
        request: Status update request
        db: Database session
        
    Returns:
        Update confirmation
    """
    try:
        # Update assignment status in workflow
        success = assignment_workflow.update_assignment_status(
            request.assignment_id,
            AssignmentStatus(request.new_status),
            request.updated_by,
            request.notes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Update database if needed
        # This would sync workflow state back to database
        
        logger.info(f"Updated assignment {request.assignment_id} status to {request.new_status}")
        return {
            "status": "success",
            "message": f"Assignment status updated to {request.new_status}",
            "assignment_id": request.assignment_id
        }
        
    except Exception as e:
        logger.error(f"Error updating assignment status: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating assignment status: {str(e)}")


@router.post("/bulk-action")
async def bulk_action_exceptions(
    request: BulkActionRequest,
    db: Session = Depends(get_db)
):
    """
    Perform bulk actions on multiple exceptions.
    
    Args:
        request: Bulk action request
        db: Database session
        
    Returns:
        Bulk action results
    """
    try:
        # Get exceptions for bulk action
        exceptions = db.query(ReconException).filter(
            ReconException.id.in_(request.exception_ids)
        ).all()
        
        if not exceptions:
            raise HTTPException(status_code=404, detail="No exceptions found with provided IDs")
        
        updated_count = 0
        
        # Perform bulk action
        if request.action == "assign" and request.team_id:
            for exception in exceptions:
                exception.assigned_team_id = request.team_id
                exception.assigned_by = request.assigned_by
                exception.assigned_at = datetime.utcnow()
                exception.assignment_status = AssignmentStatus.ASSIGNED.value
                updated_count += 1
                
        elif request.action == "resolve":
            for exception in exceptions:
                exception.status = "RESOLVED"
                exception.resolved_at = datetime.utcnow()
                exception.resolved_by = request.assigned_by
                exception.resolution_notes = request.resolution_notes
                exception.assignment_status = AssignmentStatus.RESOLVED.value
                updated_count += 1
                
        elif request.action == "escalate":
            for exception in exceptions:
                exception.is_escalated = True
                exception.assignment_status = AssignmentStatus.ESCALATED.value
                updated_count += 1
                
        elif request.action == "close":
            for exception in exceptions:
                exception.status = "RESOLVED"
                exception.assignment_status = AssignmentStatus.CLOSED.value
                updated_count += 1
        
        db.commit()
        
        logger.info(f"Bulk action '{request.action}' applied to {updated_count} exceptions")
        return {
            "status": "success",
            "message": f"Bulk action '{request.action}' applied to {updated_count} exceptions",
            "updated_count": updated_count,
            "total_requested": len(request.exception_ids)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error performing bulk action: {e}")
        raise HTTPException(status_code=500, detail=f"Error performing bulk action: {str(e)}")


@router.get("/sla-breaches", response_model=List[SLABreachResponse])
async def get_sla_breaches(
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    severity: Optional[str] = Query(None, description="Filter by SLA severity"),
    db: Session = Depends(get_db)
):
    """
    Get current SLA breaches requiring attention.
    
    Args:
        team_id: Optional team ID filter
        severity: Optional severity filter
        db: Database session
        
    Returns:
        List of SLA breaches
    """
    try:
        # Check for SLA breaches in workflow
        breached_assignments = assignment_workflow.check_sla_breaches()
        
        # Filter results
        if team_id:
            breached_assignments = [
                a for a in breached_assignments 
                if a.assigned_team_id == team_id
            ]
        
        if severity:
            breached_assignments = [
                a for a in breached_assignments 
                if a.sla_severity.value == severity
            ]
        
        # Convert to response format
        breach_responses = []
        for assignment in breached_assignments:
            now = datetime.utcnow()
            hours_overdue = (now - assignment.sla_due_at).total_seconds() / 3600
            
            breach_response = SLABreachResponse(
                assignment_id=assignment.assignment_id,
                exception_id=assignment.exception_id,
                cluster_id=assignment.cluster_id,
                assigned_team_id=assignment.assigned_team_id,
                sla_severity=assignment.sla_severity.value,
                sla_due_at=assignment.sla_due_at,
                hours_overdue=hours_overdue,
                is_escalated=assignment.is_escalated,
                assignment_reason=assignment.assignment_reason
            )
            breach_responses.append(breach_response)
        
        logger.info(f"Found {len(breach_responses)} SLA breaches")
        return breach_responses
        
    except Exception as e:
        logger.error(f"Error getting SLA breaches: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting SLA breaches: {str(e)}")


@router.get("/team-workload/{team_id}", response_model=TeamWorkloadResponse)
async def get_team_workload(
    team_id: str,
    db: Session = Depends(get_db)
):
    """
    Get workload statistics for a specific team.
    
    Args:
        team_id: Team ID to get workload for
        db: Database session
        
    Returns:
        Team workload statistics
    """
    try:
        workload_data = assignment_workflow.get_team_workload(team_id)
        
        if not workload_data:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return TeamWorkloadResponse(**workload_data)
        
    except Exception as e:
        logger.error(f"Error getting team workload: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting team workload: {str(e)}")


@router.get("/clusters/{cluster_id}/exceptions")
async def get_cluster_exceptions(
    cluster_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all exceptions in a specific cluster.
    
    Args:
        cluster_id: Cluster ID to get exceptions for
        db: Database session
        
    Returns:
        List of exceptions in cluster
    """
    try:
        exceptions = db.query(ReconException).filter(
            ReconException.cluster_id == cluster_id
        ).all()
        
        # Convert to response format
        exception_data = []
        for exception in exceptions:
            exception_data.append({
                "id": exception.id,
                "run_id": exception.run_id,
                "status": exception.status,
                "keys_json": exception.keys_json,
                "diff_json": exception.diff_json,
                "assigned_to": exception.assigned_to,
                "assigned_at": exception.assigned_at,
                "assignment_status": exception.assignment_status,
                "sla_severity": exception.sla_severity,
                "sla_due_at": exception.sla_due_at,
                "is_sla_breached": exception.is_sla_breached,
                "is_escalated": exception.is_escalated
            })
        
        return {
            "cluster_id": cluster_id,
            "exception_count": len(exceptions),
            "exceptions": exception_data
        }
        
    except Exception as e:
        logger.error(f"Error getting cluster exceptions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cluster exceptions: {str(e)}")


@router.get("/filters/teams")
async def get_teams():
    """Get list of available teams for assignment."""
    try:
        teams = []
        for team_id, team in assignment_workflow.teams.items():
            teams.append({
                "team_id": team_id,
                "team_name": team.team_name,
                "team_type": team.team_type,
                "specializations": team.specializations,
                "capacity": team.capacity
            })
        
        return {"teams": teams}
        
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting teams: {str(e)}")


@router.get("/filters/severities")
async def get_sla_severities():
    """Get list of available SLA severities."""
    try:
        severities = [severity.value for severity in SLASeverity]
        return {"severities": severities}
        
    except Exception as e:
        logger.error(f"Error getting SLA severities: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting SLA severities: {str(e)}")


@router.get("/filters/statuses")
async def get_assignment_statuses():
    """Get list of available assignment statuses."""
    try:
        statuses = [status.value for status in AssignmentStatus]
        return {"statuses": statuses}
        
    except Exception as e:
        logger.error(f"Error getting assignment statuses: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting assignment statuses: {str(e)}")
