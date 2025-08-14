from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum

from app.models.base import BaseModel

class ReconStatus(str, enum.Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ExceptionStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"

class SLASeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class AssignmentStatus(str, enum.Enum):
    UNASSIGNED = "UNASSIGNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class ReconRun(BaseModel):
    """Model for reconciliation runs."""
    __tablename__ = "recon_runs"
    
    # Run details
    status = Column(SQLEnum(ReconStatus), default=ReconStatus.RUNNING, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    
    # File references
    internal_file_id = Column(UUID(as_uuid=True), nullable=False)
    cleared_file_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Configuration (JSON stored as text)
    column_map = Column(Text, nullable=True)  # JSON string of column mappings
    match_keys = Column(Text, nullable=True)  # JSON array of match keys
    tolerances = Column(Text, nullable=True)  # JSON object of tolerances
    
    # Results summary (JSON stored as text)
    summary_json = Column(Text, nullable=True)  # JSON with total, matched, mismatched, etc.
    
    # Error information
    error_message = Column(Text, nullable=True)

class ReconException(BaseModel):
    """Model for reconciliation exceptions/breaks."""
    __tablename__ = "recon_exceptions"
    
    # Reference to reconciliation run
    run_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Exception details (JSON stored as text)
    keys_json = Column(Text, nullable=False)  # JSON of matching keys
    internal_json = Column(Text, nullable=True)  # JSON of internal record
    cleared_json = Column(Text, nullable=True)  # JSON of cleared record
    diff_json = Column(Text, nullable=True)  # JSON of differences
    
    # Status and resolution
    status = Column(SQLEnum(ExceptionStatus), default=ExceptionStatus.OPEN, nullable=False)
    
    # Assignment and resolution
    assigned_to = Column(String(255), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Clustering fields (Work Order 4)
    cluster_id = Column(String(255), nullable=True, index=True)
    cluster_key = Column(String(500), nullable=True)
    clustering_method = Column(String(50), nullable=True)
    cluster_confidence = Column(Float, nullable=True)
    
    # SLA and workflow fields (Work Order 4)
    assignment_status = Column(SQLEnum(AssignmentStatus), default=AssignmentStatus.UNASSIGNED, nullable=False)
    sla_severity = Column(SQLEnum(SLASeverity), default=SLASeverity.MEDIUM, nullable=False)
    sla_due_at = Column(DateTime, nullable=True)
    escalation_due_at = Column(DateTime, nullable=True)
    is_sla_breached = Column(Boolean, default=False, nullable=False)
    is_escalated = Column(Boolean, default=False, nullable=False)
    
    # Assignment metadata
    assigned_team_id = Column(String(255), nullable=True)
    assignment_reason = Column(Text, nullable=True)
    assignment_confidence = Column(Float, nullable=True)
    manual_override = Column(Boolean, default=False, nullable=False)
