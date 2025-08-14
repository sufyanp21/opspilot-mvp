"""API endpoints for audit and lineage tracking."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid

from app.database import get_db
from app.models.audit import (
    AuditEvent, AuditChain, LineageNode, LineageRelation, 
    AuditExport, AuditEventTypeEnum, AuditSeverityEnum,
    LineageNodeTypeEnum, LineageRelationTypeEnum
)
from app.audit.audit_logger import audit_logger, AuditEventType, AuditSeverity
from app.audit.lineage_tracker import lineage_tracker, LineageNodeType, LineageRelationType

router = APIRouter(prefix="/audit", tags=["audit"])


# Pydantic models for API requests/responses

class AuditEventResponse(BaseModel):
    """Response model for audit events."""
    event_id: str
    event_type: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    entity_type: str
    entity_id: str
    action: str
    severity: str
    description: str
    metadata: Optional[Dict[str, Any]]
    input_entities: Optional[List[str]]
    output_entities: Optional[List[str]]
    previous_hash: Optional[str]
    event_hash: str
    system_version: str
    hostname: str
    process_id: str

    class Config:
        from_attributes = True


class LineageNodeResponse(BaseModel):
    """Response model for lineage nodes."""
    node_id: str
    node_type: str
    entity_id: str
    entity_type: str
    name: str
    description: Optional[str]
    created_at: datetime
    created_by: Optional[str]
    metadata: Optional[Dict[str, Any]]
    record_count: Optional[int]
    file_size: Optional[int]
    checksum: Optional[str]
    processing_duration: Optional[float]
    processing_status: str
    error_message: Optional[str]

    class Config:
        from_attributes = True


class LineageRelationResponse(BaseModel):
    """Response model for lineage relations."""
    relation_id: str
    source_node_id: str
    target_node_id: str
    relation_type: str
    created_at: datetime
    transformation_logic: Optional[str]
    transformation_config: Optional[Dict[str, Any]]
    data_flow_metrics: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class LineageGraphResponse(BaseModel):
    """Response model for lineage graphs."""
    nodes: List[LineageNodeResponse]
    relations: List[LineageRelationResponse]
    root_node_id: str
    total_nodes: int
    total_relations: int


class AuditEventFilter(BaseModel):
    """Filter parameters for audit events."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    entity_ids: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    severities: Optional[List[str]] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class AuditExportRequest(BaseModel):
    """Request model for audit exports."""
    export_type: str = Field(..., regex="^(AUDIT|LINEAGE|COMBINED)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    entity_types: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    include_metadata: bool = True
    format: str = Field(default="JSON", regex="^(JSON|CSV)$")


class ChainIntegrityResponse(BaseModel):
    """Response model for chain integrity verification."""
    is_valid: bool
    total_events: int
    verified_events: int
    broken_links: List[str]
    verification_timestamp: datetime


# API Endpoints

@router.get("/events", response_model=List[AuditEventResponse])
async def get_audit_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_types: Optional[List[str]] = Query(None),
    entity_types: Optional[List[str]] = Query(None),
    entity_ids: Optional[List[str]] = Query(None),
    user_ids: Optional[List[str]] = Query(None),
    severities: Optional[List[str]] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get audit events with optional filtering."""
    try:
        query = db.query(AuditEvent)
        
        # Apply filters
        if start_date:
            query = query.filter(AuditEvent.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditEvent.timestamp <= end_date)
        if event_types:
            query = query.filter(AuditEvent.event_type.in_(event_types))
        if entity_types:
            query = query.filter(AuditEvent.entity_type.in_(entity_types))
        if entity_ids:
            query = query.filter(AuditEvent.entity_id.in_(entity_ids))
        if user_ids:
            query = query.filter(AuditEvent.user_id.in_(user_ids))
        if severities:
            query = query.filter(AuditEvent.severity.in_(severities))
        
        # Order by timestamp descending
        query = query.order_by(AuditEvent.timestamp.desc())
        
        # Apply pagination
        events = query.offset(offset).limit(limit).all()
        
        return [
            AuditEventResponse(
                event_id=str(event.event_id),
                event_type=event.event_type.value,
                timestamp=event.timestamp,
                user_id=event.user_id,
                session_id=event.session_id,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                action=event.action,
                severity=event.severity.value,
                description=event.description,
                metadata=event.metadata,
                input_entities=event.input_entities,
                output_entities=event.output_entities,
                previous_hash=event.previous_hash,
                event_hash=event.event_hash,
                system_version=event.system_version,
                hostname=event.hostname,
                process_id=event.process_id
            )
            for event in events
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving audit events: {str(e)}")


@router.get("/events/{event_id}", response_model=AuditEventResponse)
async def get_audit_event(event_id: str, db: Session = Depends(get_db)):
    """Get a specific audit event by ID."""
    try:
        event = db.query(AuditEvent).filter(AuditEvent.event_id == uuid.UUID(event_id)).first()
        
        if not event:
            raise HTTPException(status_code=404, detail="Audit event not found")
        
        return AuditEventResponse(
            event_id=str(event.event_id),
            event_type=event.event_type.value,
            timestamp=event.timestamp,
            user_id=event.user_id,
            session_id=event.session_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            action=event.action,
            severity=event.severity.value,
            description=event.description,
            metadata=event.metadata,
            input_entities=event.input_entities,
            output_entities=event.output_entities,
            previous_hash=event.previous_hash,
            event_hash=event.event_hash,
            system_version=event.system_version,
            hostname=event.hostname,
            process_id=event.process_id
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving audit event: {str(e)}")


@router.get("/lineage/nodes", response_model=List[LineageNodeResponse])
async def get_lineage_nodes(
    node_types: Optional[List[str]] = Query(None),
    entity_types: Optional[List[str]] = Query(None),
    entity_ids: Optional[List[str]] = Query(None),
    created_by: Optional[List[str]] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get lineage nodes with optional filtering."""
    try:
        query = db.query(LineageNode)
        
        # Apply filters
        if node_types:
            query = query.filter(LineageNode.node_type.in_(node_types))
        if entity_types:
            query = query.filter(LineageNode.entity_type.in_(entity_types))
        if entity_ids:
            query = query.filter(LineageNode.entity_id.in_(entity_ids))
        if created_by:
            query = query.filter(LineageNode.created_by.in_(created_by))
        
        # Order by creation time descending
        query = query.order_by(LineageNode.created_at.desc())
        
        # Apply pagination
        nodes = query.offset(offset).limit(limit).all()
        
        return [
            LineageNodeResponse(
                node_id=str(node.node_id),
                node_type=node.node_type.value,
                entity_id=node.entity_id,
                entity_type=node.entity_type,
                name=node.name,
                description=node.description,
                created_at=node.created_at,
                created_by=node.created_by,
                metadata=node.metadata,
                record_count=node.record_count,
                file_size=node.file_size,
                checksum=node.checksum,
                processing_duration=node.processing_duration,
                processing_status=node.processing_status,
                error_message=node.error_message
            )
            for node in nodes
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lineage nodes: {str(e)}")


@router.get("/lineage/nodes/{node_id}", response_model=LineageNodeResponse)
async def get_lineage_node(node_id: str, db: Session = Depends(get_db)):
    """Get a specific lineage node by ID."""
    try:
        node = db.query(LineageNode).filter(LineageNode.node_id == uuid.UUID(node_id)).first()
        
        if not node:
            raise HTTPException(status_code=404, detail="Lineage node not found")
        
        return LineageNodeResponse(
            node_id=str(node.node_id),
            node_type=node.node_type.value,
            entity_id=node.entity_id,
            entity_type=node.entity_type,
            name=node.name,
            description=node.description,
            created_at=node.created_at,
            created_by=node.created_by,
            metadata=node.metadata,
            record_count=node.record_count,
            file_size=node.file_size,
            checksum=node.checksum,
            processing_duration=node.processing_duration,
            processing_status=node.processing_status,
            error_message=node.error_message
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid node ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lineage node: {str(e)}")


@router.get("/lineage/nodes/{node_id}/upstream", response_model=List[LineageNodeResponse])
async def get_upstream_lineage(
    node_id: str, 
    max_depth: int = Query(10, le=20),
    db: Session = Depends(get_db)
):
    """Get upstream lineage (ancestors) for a node."""
    try:
        # Verify node exists
        node = db.query(LineageNode).filter(LineageNode.node_id == uuid.UUID(node_id)).first()
        if not node:
            raise HTTPException(status_code=404, detail="Lineage node not found")
        
        # Get upstream nodes using lineage tracker
        upstream_nodes = lineage_tracker.get_upstream_lineage(node_id, max_depth)
        
        return [
            LineageNodeResponse(
                node_id=str(node.node_id),
                node_type=node.node_type.value,
                entity_id=node.entity_id,
                entity_type=node.entity_type,
                name=node.name,
                description=node.description,
                created_at=node.created_at,
                created_by=node.created_by,
                metadata=node.metadata,
                record_count=node.record_count,
                file_size=node.file_size,
                checksum=node.checksum,
                processing_duration=node.processing_duration,
                processing_status=node.processing_status,
                error_message=node.error_message
            )
            for node in upstream_nodes
        ]
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid node ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving upstream lineage: {str(e)}")


@router.get("/lineage/nodes/{node_id}/downstream", response_model=List[LineageNodeResponse])
async def get_downstream_lineage(
    node_id: str, 
    max_depth: int = Query(10, le=20),
    db: Session = Depends(get_db)
):
    """Get downstream lineage (descendants) for a node."""
    try:
        # Verify node exists
        node = db.query(LineageNode).filter(LineageNode.node_id == uuid.UUID(node_id)).first()
        if not node:
            raise HTTPException(status_code=404, detail="Lineage node not found")
        
        # Get downstream nodes using lineage tracker
        downstream_nodes = lineage_tracker.get_downstream_lineage(node_id, max_depth)
        
        return [
            LineageNodeResponse(
                node_id=str(node.node_id),
                node_type=node.node_type.value,
                entity_id=node.entity_id,
                entity_type=node.entity_type,
                name=node.name,
                description=node.description,
                created_at=node.created_at,
                created_by=node.created_by,
                metadata=node.metadata,
                record_count=node.record_count,
                file_size=node.file_size,
                checksum=node.checksum,
                processing_duration=node.processing_duration,
                processing_status=node.processing_status,
                error_message=node.error_message
            )
            for node in downstream_nodes
        ]
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid node ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving downstream lineage: {str(e)}")


@router.get("/lineage/graphs/{node_id}", response_model=LineageGraphResponse)
async def get_lineage_graph(node_id: str, db: Session = Depends(get_db)):
    """Get complete lineage graph for a node."""
    try:
        # Verify node exists
        node = db.query(LineageNode).filter(LineageNode.node_id == uuid.UUID(node_id)).first()
        if not node:
            raise HTTPException(status_code=404, detail="Lineage node not found")
        
        # Get complete lineage graph
        graph = lineage_tracker.get_lineage_graph(node_id)
        
        # Convert to response format
        nodes = [
            LineageNodeResponse(
                node_id=str(node.node_id),
                node_type=node.node_type.value,
                entity_id=node.entity_id,
                entity_type=node.entity_type,
                name=node.name,
                description=node.description,
                created_at=node.created_at,
                created_by=node.created_by,
                metadata=node.metadata,
                record_count=node.record_count,
                file_size=node.file_size,
                checksum=node.checksum,
                processing_duration=node.processing_duration,
                processing_status=node.processing_status,
                error_message=node.error_message
            )
            for node in graph.nodes.values()
        ]
        
        relations = [
            LineageRelationResponse(
                relation_id=str(relation.relation_id),
                source_node_id=str(relation.source_node_id),
                target_node_id=str(relation.target_node_id),
                relation_type=relation.relation_type.value,
                created_at=relation.created_at,
                transformation_logic=relation.transformation_logic,
                transformation_config=relation.transformation_config,
                data_flow_metrics=relation.data_flow_metrics
            )
            for relation in graph.relations.values()
        ]
        
        return LineageGraphResponse(
            nodes=nodes,
            relations=relations,
            root_node_id=str(graph.root_node_id),
            total_nodes=len(nodes),
            total_relations=len(relations)
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid node ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lineage graph: {str(e)}")


@router.get("/entity/{entity_type}/{entity_id}/lineage", response_model=List[AuditEventResponse])
async def get_entity_audit_lineage(
    entity_type: str, 
    entity_id: str, 
    db: Session = Depends(get_db)
):
    """Get complete audit lineage for a specific entity."""
    try:
        # Get audit events for the entity
        events = db.query(AuditEvent).filter(
            AuditEvent.entity_type == entity_type,
            AuditEvent.entity_id == entity_id
        ).order_by(AuditEvent.timestamp.asc()).all()
        
        # Also get events where this entity is in input/output lineage
        related_events = db.query(AuditEvent).filter(
            (AuditEvent.input_entities.contains([entity_id])) |
            (AuditEvent.output_entities.contains([entity_id]))
        ).order_by(AuditEvent.timestamp.asc()).all()
        
        # Combine and deduplicate
        all_events = {event.event_id: event for event in events + related_events}
        sorted_events = sorted(all_events.values(), key=lambda e: e.timestamp)
        
        return [
            AuditEventResponse(
                event_id=str(event.event_id),
                event_type=event.event_type.value,
                timestamp=event.timestamp,
                user_id=event.user_id,
                session_id=event.session_id,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                action=event.action,
                severity=event.severity.value,
                description=event.description,
                metadata=event.metadata,
                input_entities=event.input_entities,
                output_entities=event.output_entities,
                previous_hash=event.previous_hash,
                event_hash=event.event_hash,
                system_version=event.system_version,
                hostname=event.hostname,
                process_id=event.process_id
            )
            for event in sorted_events
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving entity lineage: {str(e)}")


@router.post("/verify-integrity", response_model=ChainIntegrityResponse)
async def verify_chain_integrity(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Verify the integrity of the audit event chain."""
    try:
        # Get events to verify
        query = db.query(AuditEvent).order_by(AuditEvent.timestamp.asc())
        
        if start_date:
            query = query.filter(AuditEvent.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditEvent.timestamp <= end_date)
        
        events = query.all()
        
        # Convert to audit logger format for verification
        audit_events = []
        for event in events:
            audit_events.append(event)  # Simplified for MVP
        
        # Verify chain integrity
        is_valid = audit_logger.verify_chain_integrity(audit_events)
        
        return ChainIntegrityResponse(
            is_valid=is_valid,
            total_events=len(events),
            verified_events=len(events) if is_valid else 0,
            broken_links=[],  # Would implement detailed analysis
            verification_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying chain integrity: {str(e)}")


@router.post("/export", response_model=Dict[str, Any])
async def export_audit_data(
    export_request: AuditExportRequest,
    db: Session = Depends(get_db)
):
    """Export audit and lineage data."""
    try:
        # Create export using audit logger
        export_data = audit_logger.export_audit_pack(
            start_date=export_request.start_date,
            end_date=export_request.end_date,
            entity_types=export_request.entity_types,
            event_types=[AuditEventType(et) for et in export_request.event_types] if export_request.event_types else None
        )
        
        # If lineage data requested, add it
        if export_request.export_type in ["LINEAGE", "COMBINED"]:
            lineage_data = lineage_tracker.export_lineage_data(
                include_metadata=export_request.include_metadata
            )
            export_data["lineage"] = lineage_data
        
        # Log the export action
        audit_logger.log_event(
            event_type=AuditEventType.DATA_EXPORT,
            entity_type="AuditExport",
            entity_id=export_data["export_metadata"]["export_id"],
            action="EXPORT",
            description=f"Exported {export_request.export_type} data",
            severity=AuditSeverity.MEDIUM,
            metadata={
                "export_type": export_request.export_type,
                "format": export_request.format,
                "date_range": {
                    "start": export_request.start_date.isoformat() if export_request.start_date else None,
                    "end": export_request.end_date.isoformat() if export_request.end_date else None
                }
            }
        )
        
        return export_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting audit data: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_audit_stats(db: Session = Depends(get_db)):
    """Get audit and lineage statistics."""
    try:
        # Get basic counts
        total_events = db.query(AuditEvent).count()
        total_nodes = db.query(LineageNode).count()
        total_relations = db.query(LineageRelation).count()
        
        # Get recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_events = db.query(AuditEvent).filter(
            AuditEvent.timestamp >= yesterday
        ).count()
        
        # Get event type distribution
        event_type_stats = db.query(
            AuditEvent.event_type, 
            db.func.count(AuditEvent.id)
        ).group_by(AuditEvent.event_type).all()
        
        # Get node type distribution
        node_type_stats = db.query(
            LineageNode.node_type,
            db.func.count(LineageNode.id)
        ).group_by(LineageNode.node_type).all()
        
        return {
            "summary": {
                "total_audit_events": total_events,
                "total_lineage_nodes": total_nodes,
                "total_lineage_relations": total_relations,
                "recent_events_24h": recent_events
            },
            "event_types": {
                event_type.value: count for event_type, count in event_type_stats
            },
            "node_types": {
                node_type.value: count for node_type, count in node_type_stats
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving audit stats: {str(e)}")
