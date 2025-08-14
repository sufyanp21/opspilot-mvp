"""Database models for audit and lineage tracking."""

from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

from app.models.base import BaseModel


class AuditEventTypeEnum(Enum):
    """Types of audit events."""
    FILE_UPLOAD = "FILE_UPLOAD"
    RECONCILIATION_RUN = "RECONCILIATION_RUN"
    EXCEPTION_CREATED = "EXCEPTION_CREATED"
    EXCEPTION_RESOLVED = "EXCEPTION_RESOLVED"
    EXCEPTION_ASSIGNED = "EXCEPTION_ASSIGNED"
    CLUSTERING_RUN = "CLUSTERING_RUN"
    SLA_BREACH = "SLA_BREACH"
    BULK_OPERATION = "BULK_OPERATION"
    DATA_EXPORT = "DATA_EXPORT"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    USER_ACTION = "USER_ACTION"
    SYSTEM_ACTION = "SYSTEM_ACTION"


class AuditSeverityEnum(Enum):
    """Severity levels for audit events."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LineageNodeTypeEnum(Enum):
    """Types of nodes in the lineage graph."""
    SOURCE_FILE = "SOURCE_FILE"
    PARSED_DATA = "PARSED_DATA"
    TRANSFORMED_DATA = "TRANSFORMED_DATA"
    RECONCILIATION_RUN = "RECONCILIATION_RUN"
    EXCEPTION = "EXCEPTION"
    CLUSTER = "CLUSTER"
    ASSIGNMENT = "ASSIGNMENT"
    REPORT = "REPORT"
    EXPORT = "EXPORT"


class LineageRelationTypeEnum(Enum):
    """Types of relationships between lineage nodes."""
    DERIVED_FROM = "DERIVED_FROM"
    TRANSFORMED_TO = "TRANSFORMED_TO"
    GENERATED_BY = "GENERATED_BY"
    CONTAINS = "CONTAINS"
    GROUPED_INTO = "GROUPED_INTO"
    ASSIGNED_TO = "ASSIGNED_TO"
    EXPORTED_AS = "EXPORT_AS"


class AuditEvent(BaseModel):
    """Immutable audit event record."""
    __tablename__ = "audit_events"
    
    # Primary identification
    event_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    event_type = Column(SQLEnum(AuditEventTypeEnum), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # User and session context
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Entity information
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    
    # Event details
    severity = Column(SQLEnum(AuditSeverityEnum), default=AuditSeverityEnum.MEDIUM, nullable=False)
    description = Column(Text, nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Data lineage
    input_entities = Column(JSONB, nullable=True)  # List of input entity IDs
    output_entities = Column(JSONB, nullable=True)  # List of output entity IDs
    
    # Immutability and integrity
    previous_hash = Column(String(64), nullable=True)  # SHA-256 hash
    event_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    signature = Column(Text, nullable=True)  # Digital signature (optional)
    
    # System context
    system_version = Column(String(50), nullable=False)
    hostname = Column(String(255), nullable=False)
    process_id = Column(String(255), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_events_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_events_timestamp', 'timestamp'),
        Index('idx_audit_events_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_events_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_audit_events_hash_chain', 'previous_hash', 'event_hash'),
    )


class AuditChain(BaseModel):
    """Represents a chain of related audit events."""
    __tablename__ = "audit_chains"
    
    chain_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    chain_type = Column(String(100), nullable=False, index=True)
    root_event_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Chain metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    chain_hash = Column(String(64), nullable=False)  # Hash of entire chain
    
    # Event count for quick reference
    event_count = Column(Integer, default=0, nullable=False)
    
    # Chain status
    is_complete = Column(Boolean, default=False, nullable=False)
    completion_timestamp = Column(DateTime, nullable=True)


class LineageNode(BaseModel):
    """Represents a node in the data lineage graph."""
    __tablename__ = "lineage_nodes"
    
    # Primary identification
    node_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    node_type = Column(SQLEnum(LineageNodeTypeEnum), nullable=False, index=True)
    
    # Entity reference
    entity_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    
    # Node information
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = Column(String(255), nullable=True, index=True)
    
    # Node metadata
    metadata = Column(JSONB, nullable=True)
    
    # Data characteristics
    record_count = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    checksum = Column(String(64), nullable=True)  # SHA-256 checksum
    
    # Processing information
    processing_duration = Column(Float, nullable=True)  # Duration in seconds
    processing_status = Column(String(50), default="COMPLETED", nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    source_relations = relationship(
        "LineageRelation", 
        foreign_keys="LineageRelation.source_node_id",
        back_populates="source_node"
    )
    target_relations = relationship(
        "LineageRelation", 
        foreign_keys="LineageRelation.target_node_id",
        back_populates="target_node"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_lineage_nodes_entity', 'entity_type', 'entity_id'),
        Index('idx_lineage_nodes_type_created', 'node_type', 'created_at'),
        Index('idx_lineage_nodes_created_by', 'created_by', 'created_at'),
    )


class LineageRelation(BaseModel):
    """Represents a relationship between two lineage nodes."""
    __tablename__ = "lineage_relations"
    
    # Primary identification
    relation_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    # Node references
    source_node_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('lineage_nodes.node_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    target_node_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('lineage_nodes.node_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Relationship information
    relation_type = Column(SQLEnum(LineageRelationTypeEnum), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Transformation details
    transformation_logic = Column(Text, nullable=True)
    transformation_config = Column(JSONB, nullable=True)
    data_flow_metrics = Column(JSONB, nullable=True)
    
    # Relationships
    source_node = relationship(
        "LineageNode", 
        foreign_keys=[source_node_id],
        back_populates="source_relations"
    )
    target_node = relationship(
        "LineageNode", 
        foreign_keys=[target_node_id],
        back_populates="target_relations"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_lineage_relations_source_target', 'source_node_id', 'target_node_id'),
        Index('idx_lineage_relations_type_created', 'relation_type', 'created_at'),
        # Prevent duplicate relations
        Index('idx_lineage_relations_unique', 'source_node_id', 'target_node_id', 'relation_type', unique=True),
    )


class LineageGraph(BaseModel):
    """Represents a complete lineage graph snapshot."""
    __tablename__ = "lineage_graphs"
    
    # Primary identification
    graph_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    root_node_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('lineage_nodes.node_id'),
        nullable=False,
        index=True
    )
    
    # Graph metadata
    graph_type = Column(String(100), nullable=True, index=True)  # e.g., "reconciliation_run", "exception_lifecycle"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Graph statistics
    node_count = Column(Integer, default=0, nullable=False)
    relation_count = Column(Integer, default=0, nullable=False)
    max_depth = Column(Integer, default=0, nullable=False)
    
    # Graph data (denormalized for performance)
    graph_data = Column(JSONB, nullable=True)  # Complete graph structure
    
    # Graph integrity
    graph_hash = Column(String(64), nullable=False)  # Hash of graph structure
    
    # Relationship to root node
    root_node = relationship("LineageNode", foreign_keys=[root_node_id])


class AuditExport(BaseModel):
    """Tracks audit data exports for compliance and backup."""
    __tablename__ = "audit_exports"
    
    # Primary identification
    export_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    export_type = Column(String(50), nullable=False, index=True)  # "AUDIT", "LINEAGE", "COMBINED"
    
    # Export metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = Column(String(255), nullable=True, index=True)
    
    # Export parameters
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    entity_types = Column(JSONB, nullable=True)  # List of entity types
    event_types = Column(JSONB, nullable=True)  # List of event types
    
    # Export results
    total_events = Column(Integer, default=0, nullable=False)
    total_nodes = Column(Integer, default=0, nullable=False)
    total_relations = Column(Integer, default=0, nullable=False)
    
    # Export integrity
    export_hash = Column(String(64), nullable=False)  # Hash of exported data
    chain_integrity_verified = Column(Boolean, default=False, nullable=False)
    
    # Export storage
    file_path = Column(String(1000), nullable=True)  # Path to exported file
    file_size = Column(Integer, nullable=True)  # Size in bytes
    compression_type = Column(String(20), nullable=True)  # e.g., "gzip", "zip"
    
    # Export status
    status = Column(String(50), default="COMPLETED", nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_exports_type_created', 'export_type', 'created_at'),
        Index('idx_audit_exports_created_by', 'created_by', 'created_at'),
        Index('idx_audit_exports_date_range', 'start_date', 'end_date'),
    )


# Additional utility models for audit trail management

class AuditRetentionPolicy(BaseModel):
    """Defines retention policies for audit data."""
    __tablename__ = "audit_retention_policies"
    
    policy_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    policy_name = Column(String(255), nullable=False, unique=True)
    
    # Retention rules
    event_types = Column(JSONB, nullable=True)  # Specific event types (null = all)
    entity_types = Column(JSONB, nullable=True)  # Specific entity types (null = all)
    severity_levels = Column(JSONB, nullable=True)  # Specific severities (null = all)
    
    # Retention periods
    retention_days = Column(Integer, nullable=False)  # Days to retain
    archive_after_days = Column(Integer, nullable=True)  # Days before archiving
    
    # Policy status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AuditArchive(BaseModel):
    """Tracks archived audit data."""
    __tablename__ = "audit_archives"
    
    archive_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    archive_name = Column(String(255), nullable=False)
    
    # Archive metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    archive_date_start = Column(DateTime, nullable=False, index=True)
    archive_date_end = Column(DateTime, nullable=False, index=True)
    
    # Archive statistics
    total_events = Column(Integer, default=0, nullable=False)
    total_nodes = Column(Integer, default=0, nullable=False)
    total_relations = Column(Integer, default=0, nullable=False)
    
    # Archive storage
    storage_location = Column(String(1000), nullable=False)
    compressed_size = Column(Integer, nullable=True)  # Size in bytes
    compression_ratio = Column(Float, nullable=True)
    
    # Archive integrity
    archive_hash = Column(String(64), nullable=False)
    verification_status = Column(String(50), default="VERIFIED", nullable=False)
    
    # Archive status
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, RESTORED, DELETED
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_archives_date_range', 'archive_date_start', 'archive_date_end'),
        Index('idx_audit_archives_created', 'created_at'),
    )
