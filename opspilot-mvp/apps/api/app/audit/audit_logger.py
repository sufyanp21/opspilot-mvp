"""Immutable audit logging system for OpsPilot MVP."""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
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


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class AuditEvent:
    """Immutable audit event record."""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    
    # Event details
    entity_type: str  # e.g., "ReconRun", "Exception", "File"
    entity_id: str
    action: str  # e.g., "CREATE", "UPDATE", "DELETE", "ASSIGN"
    
    # Context and metadata
    severity: AuditSeverity
    description: str
    metadata: Dict[str, Any]
    
    # Data lineage
    input_entities: List[str]  # IDs of input entities
    output_entities: List[str]  # IDs of output entities
    
    # Immutability and integrity
    previous_hash: Optional[str]  # Hash of previous event in chain
    event_hash: str  # Hash of this event
    signature: Optional[str]  # Digital signature (optional)
    
    # System context
    system_version: str
    hostname: str
    process_id: str


@dataclass
class AuditChain:
    """Represents a chain of related audit events."""
    chain_id: str
    chain_type: str  # e.g., "reconciliation_run", "exception_lifecycle"
    root_event_id: str
    events: List[AuditEvent]
    created_at: datetime
    updated_at: datetime
    chain_hash: str  # Hash of entire chain


class AuditLogger:
    """Immutable audit logging system with hash chain verification."""
    
    def __init__(self, storage_backend=None):
        self.storage_backend = storage_backend
        self.event_chain: List[AuditEvent] = []
        self.chain_hashes: Dict[str, str] = {}
        
    def log_event(
        self,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: str,
        action: str,
        description: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        input_entities: Optional[List[str]] = None,
        output_entities: Optional[List[str]] = None
    ) -> AuditEvent:
        """
        Log an immutable audit event.
        
        Args:
            event_type: Type of audit event
            entity_type: Type of entity being audited
            entity_id: ID of the entity
            action: Action being performed
            description: Human-readable description
            user_id: ID of user performing action (if applicable)
            session_id: Session ID (if applicable)
            severity: Severity level of the event
            metadata: Additional metadata
            input_entities: List of input entity IDs for lineage
            output_entities: List of output entity IDs for lineage
            
        Returns:
            Created audit event
        """
        try:
            # Generate event ID
            event_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            # Get previous hash for chain integrity
            previous_hash = self._get_last_hash()
            
            # Prepare event data
            event_data = {
                "event_id": event_id,
                "event_type": event_type.value,
                "timestamp": timestamp.isoformat(),
                "user_id": user_id,
                "session_id": session_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "severity": severity.value,
                "description": description,
                "metadata": metadata or {},
                "input_entities": input_entities or [],
                "output_entities": output_entities or [],
                "previous_hash": previous_hash,
                "system_version": "1.0.0",  # Would come from config
                "hostname": "localhost",    # Would come from system
                "process_id": str(uuid.uuid4())  # Simplified for MVP
            }
            
            # Calculate event hash
            event_hash = self._calculate_event_hash(event_data)
            event_data["event_hash"] = event_hash
            
            # Create audit event
            audit_event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=timestamp,
                user_id=user_id,
                session_id=session_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                severity=severity,
                description=description,
                metadata=metadata or {},
                input_entities=input_entities or [],
                output_entities=output_entities or [],
                previous_hash=previous_hash,
                event_hash=event_hash,
                signature=None,  # Would implement digital signing in production
                system_version=event_data["system_version"],
                hostname=event_data["hostname"],
                process_id=event_data["process_id"]
            )
            
            # Add to chain
            self.event_chain.append(audit_event)
            
            # Store event (would persist to database in production)
            if self.storage_backend:
                self.storage_backend.store_event(audit_event)
            
            logger.info(f"Audit event logged: {event_type.value} for {entity_type}:{entity_id}")
            return audit_event
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            raise
    
    def verify_chain_integrity(self, events: Optional[List[AuditEvent]] = None) -> bool:
        """
        Verify the integrity of the audit event chain.
        
        Args:
            events: List of events to verify (defaults to current chain)
            
        Returns:
            True if chain is valid, False otherwise
        """
        try:
            events_to_verify = events or self.event_chain
            
            if not events_to_verify:
                return True
            
            # Verify each event's hash
            for i, event in enumerate(events_to_verify):
                # Reconstruct event data for hash verification
                event_data = {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "user_id": event.user_id,
                    "session_id": event.session_id,
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "action": event.action,
                    "severity": event.severity.value,
                    "description": event.description,
                    "metadata": event.metadata,
                    "input_entities": event.input_entities,
                    "output_entities": event.output_entities,
                    "previous_hash": event.previous_hash,
                    "system_version": event.system_version,
                    "hostname": event.hostname,
                    "process_id": event.process_id
                }
                
                # Verify event hash
                calculated_hash = self._calculate_event_hash(event_data)
                if calculated_hash != event.event_hash:
                    logger.error(f"Hash mismatch for event {event.event_id}")
                    return False
                
                # Verify chain linkage (except for first event)
                if i > 0:
                    expected_previous_hash = events_to_verify[i-1].event_hash
                    if event.previous_hash != expected_previous_hash:
                        logger.error(f"Chain linkage broken at event {event.event_id}")
                        return False
            
            logger.info(f"Verified integrity of {len(events_to_verify)} audit events")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying chain integrity: {e}")
            return False
    
    def get_entity_lineage(self, entity_id: str, entity_type: str) -> List[AuditEvent]:
        """
        Get the complete audit lineage for an entity.
        
        Args:
            entity_id: ID of the entity
            entity_type: Type of the entity
            
        Returns:
            List of audit events related to the entity
        """
        try:
            # Find all events related to this entity
            related_events = []
            
            for event in self.event_chain:
                # Direct entity match
                if event.entity_id == entity_id and event.entity_type == entity_type:
                    related_events.append(event)
                # Input/output lineage match
                elif entity_id in event.input_entities or entity_id in event.output_entities:
                    related_events.append(event)
            
            # Sort by timestamp
            related_events.sort(key=lambda e: e.timestamp)
            
            logger.info(f"Found {len(related_events)} lineage events for {entity_type}:{entity_id}")
            return related_events
            
        except Exception as e:
            logger.error(f"Error getting entity lineage: {e}")
            return []
    
    def create_audit_chain(
        self, 
        chain_type: str, 
        root_event_id: str, 
        related_events: List[AuditEvent]
    ) -> AuditChain:
        """
        Create an audit chain for related events.
        
        Args:
            chain_type: Type of the chain
            root_event_id: ID of the root event
            related_events: List of related events
            
        Returns:
            Created audit chain
        """
        try:
            chain_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Calculate chain hash
            chain_data = {
                "chain_id": chain_id,
                "chain_type": chain_type,
                "root_event_id": root_event_id,
                "event_ids": [e.event_id for e in related_events],
                "created_at": now.isoformat()
            }
            
            chain_hash = hashlib.sha256(
                json.dumps(chain_data, sort_keys=True).encode()
            ).hexdigest()
            
            audit_chain = AuditChain(
                chain_id=chain_id,
                chain_type=chain_type,
                root_event_id=root_event_id,
                events=related_events,
                created_at=now,
                updated_at=now,
                chain_hash=chain_hash
            )
            
            # Store chain hash for verification
            self.chain_hashes[chain_id] = chain_hash
            
            logger.info(f"Created audit chain {chain_id} with {len(related_events)} events")
            return audit_chain
            
        except Exception as e:
            logger.error(f"Error creating audit chain: {e}")
            raise
    
    def export_audit_pack(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        entity_types: Optional[List[str]] = None,
        event_types: Optional[List[AuditEventType]] = None
    ) -> Dict[str, Any]:
        """
        Export audit data as a verifiable package.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            entity_types: Entity type filters
            event_types: Event type filters
            
        Returns:
            Audit package with events and verification data
        """
        try:
            # Filter events
            filtered_events = self.event_chain.copy()
            
            if start_date:
                filtered_events = [e for e in filtered_events if e.timestamp >= start_date]
            
            if end_date:
                filtered_events = [e for e in filtered_events if e.timestamp <= end_date]
            
            if entity_types:
                filtered_events = [e for e in filtered_events if e.entity_type in entity_types]
            
            if event_types:
                filtered_events = [e for e in filtered_events if e.event_type in event_types]
            
            # Create export package
            export_package = {
                "export_metadata": {
                    "export_id": str(uuid.uuid4()),
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "total_events": len(filtered_events),
                    "date_range": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None
                    },
                    "filters": {
                        "entity_types": entity_types,
                        "event_types": [et.value for et in event_types] if event_types else None
                    }
                },
                "events": [asdict(event) for event in filtered_events],
                "verification": {
                    "chain_integrity_verified": self.verify_chain_integrity(filtered_events),
                    "export_hash": None  # Will be calculated below
                }
            }
            
            # Calculate export hash
            export_hash = hashlib.sha256(
                json.dumps(export_package["events"], sort_keys=True).encode()
            ).hexdigest()
            export_package["verification"]["export_hash"] = export_hash
            
            logger.info(f"Exported audit pack with {len(filtered_events)} events")
            return export_package
            
        except Exception as e:
            logger.error(f"Error exporting audit pack: {e}")
            raise
    
    def _get_last_hash(self) -> Optional[str]:
        """Get the hash of the last event in the chain."""
        if not self.event_chain:
            return None
        return self.event_chain[-1].event_hash
    
    def _calculate_event_hash(self, event_data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of event data."""
        # Remove hash field if present to avoid circular reference
        data_to_hash = {k: v for k, v in event_data.items() if k != "event_hash"}
        
        # Create deterministic JSON string
        json_string = json.dumps(data_to_hash, sort_keys=True, default=str)
        
        # Calculate hash
        return hashlib.sha256(json_string.encode()).hexdigest()


# Global audit logger instance
audit_logger = AuditLogger()
