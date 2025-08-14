"""Unit tests for audit logger functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import uuid
import json

from app.audit.audit_logger import (
    AuditLogger, AuditEvent, AuditChain, AuditEventType, AuditSeverity
)


class TestAuditLogger:
    """Test cases for AuditLogger class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.audit_logger = AuditLogger()
        self.test_user_id = "test_user_123"
        self.test_session_id = "session_456"
    
    def test_log_event_basic(self):
        """Test basic event logging functionality."""
        # Log a basic event
        event = self.audit_logger.log_event(
            event_type=AuditEventType.FILE_UPLOAD,
            entity_type="SourceFile",
            entity_id="file_123",
            action="CREATE",
            description="Test file upload",
            user_id=self.test_user_id,
            session_id=self.test_session_id
        )
        
        # Verify event properties
        assert event.event_type == AuditEventType.FILE_UPLOAD
        assert event.entity_type == "SourceFile"
        assert event.entity_id == "file_123"
        assert event.action == "CREATE"
        assert event.description == "Test file upload"
        assert event.user_id == self.test_user_id
        assert event.session_id == self.test_session_id
        assert event.severity == AuditSeverity.MEDIUM  # Default
        assert event.event_hash is not None
        assert event.previous_hash is None  # First event
        
        # Verify event is in chain
        assert len(self.audit_logger.event_chain) == 1
        assert self.audit_logger.event_chain[0] == event
    
    def test_log_event_with_metadata(self):
        """Test event logging with metadata and lineage."""
        metadata = {
            "file_size": 1024,
            "file_type": "CSV",
            "columns": ["trade_id", "symbol", "qty"]
        }
        
        input_entities = ["source_file_1", "source_file_2"]
        output_entities = ["parsed_data_1"]
        
        event = self.audit_logger.log_event(
            event_type=AuditEventType.RECONCILIATION_RUN,
            entity_type="ReconRun",
            entity_id="run_789",
            action="EXECUTE",
            description="Reconciliation processing",
            severity=AuditSeverity.HIGH,
            metadata=metadata,
            input_entities=input_entities,
            output_entities=output_entities
        )
        
        # Verify metadata and lineage
        assert event.metadata == metadata
        assert event.input_entities == input_entities
        assert event.output_entities == output_entities
        assert event.severity == AuditSeverity.HIGH
    
    def test_event_chain_integrity(self):
        """Test hash chain integrity across multiple events."""
        # Log first event
        event1 = self.audit_logger.log_event(
            event_type=AuditEventType.FILE_UPLOAD,
            entity_type="SourceFile",
            entity_id="file_1",
            action="CREATE",
            description="First event"
        )
        
        # Log second event
        event2 = self.audit_logger.log_event(
            event_type=AuditEventType.RECONCILIATION_RUN,
            entity_type="ReconRun",
            entity_id="run_1",
            action="EXECUTE",
            description="Second event"
        )
        
        # Log third event
        event3 = self.audit_logger.log_event(
            event_type=AuditEventType.EXCEPTION_CREATED,
            entity_type="ReconException",
            entity_id="exception_1",
            action="CREATE",
            description="Third event"
        )
        
        # Verify chain linkage
        assert event1.previous_hash is None
        assert event2.previous_hash == event1.event_hash
        assert event3.previous_hash == event2.event_hash
        
        # Verify chain integrity
        assert self.audit_logger.verify_chain_integrity() is True
    
    def test_verify_chain_integrity_valid(self):
        """Test chain integrity verification with valid chain."""
        # Create a series of events
        for i in range(5):
            self.audit_logger.log_event(
                event_type=AuditEventType.USER_ACTION,
                entity_type="TestEntity",
                entity_id=f"entity_{i}",
                action="TEST",
                description=f"Test event {i}"
            )
        
        # Verify integrity
        assert self.audit_logger.verify_chain_integrity() is True
        assert len(self.audit_logger.event_chain) == 5
    
    def test_verify_chain_integrity_broken(self):
        """Test chain integrity verification with broken chain."""
        # Create events
        event1 = self.audit_logger.log_event(
            event_type=AuditEventType.FILE_UPLOAD,
            entity_type="SourceFile",
            entity_id="file_1",
            action="CREATE",
            description="First event"
        )
        
        event2 = self.audit_logger.log_event(
            event_type=AuditEventType.RECONCILIATION_RUN,
            entity_type="ReconRun",
            entity_id="run_1",
            action="EXECUTE",
            description="Second event"
        )
        
        # Manually corrupt the chain
        event2.previous_hash = "corrupted_hash"
        
        # Verify integrity fails
        assert self.audit_logger.verify_chain_integrity() is False
    
    def test_get_entity_lineage(self):
        """Test retrieving entity lineage."""
        entity_id = "test_entity_123"
        entity_type = "TestEntity"
        
        # Log events for the entity
        event1 = self.audit_logger.log_event(
            event_type=AuditEventType.USER_ACTION,
            entity_type=entity_type,
            entity_id=entity_id,
            action="CREATE",
            description="Entity created"
        )
        
        event2 = self.audit_logger.log_event(
            event_type=AuditEventType.USER_ACTION,
            entity_type=entity_type,
            entity_id=entity_id,
            action="UPDATE",
            description="Entity updated"
        )
        
        # Log event with entity in lineage
        event3 = self.audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_ACTION,
            entity_type="OtherEntity",
            entity_id="other_123",
            action="PROCESS",
            description="Processing with entity",
            input_entities=[entity_id]
        )
        
        # Get lineage
        lineage = self.audit_logger.get_entity_lineage(entity_id, entity_type)
        
        # Verify lineage
        assert len(lineage) == 3
        assert event1 in lineage
        assert event2 in lineage
        assert event3 in lineage
        
        # Verify chronological order
        assert lineage[0].timestamp <= lineage[1].timestamp <= lineage[2].timestamp
    
    def test_create_audit_chain(self):
        """Test creating audit chains."""
        # Create related events
        events = []
        for i in range(3):
            event = self.audit_logger.log_event(
                event_type=AuditEventType.RECONCILIATION_RUN,
                entity_type="ReconRun",
                entity_id=f"run_{i}",
                action="EXECUTE",
                description=f"Reconciliation run {i}"
            )
            events.append(event)
        
        # Create audit chain
        chain = self.audit_logger.create_audit_chain(
            chain_type="reconciliation_workflow",
            root_event_id=events[0].event_id,
            related_events=events
        )
        
        # Verify chain properties
        assert chain.chain_type == "reconciliation_workflow"
        assert chain.root_event_id == events[0].event_id
        assert len(chain.events) == 3
        assert chain.chain_hash is not None
        
        # Verify chain is stored
        assert chain.chain_id in self.audit_logger.chain_hashes
    
    def test_export_audit_pack_basic(self):
        """Test basic audit pack export."""
        # Create test events
        for i in range(3):
            self.audit_logger.log_event(
                event_type=AuditEventType.FILE_UPLOAD,
                entity_type="SourceFile",
                entity_id=f"file_{i}",
                action="CREATE",
                description=f"File upload {i}"
            )
        
        # Export audit pack
        export_pack = self.audit_logger.export_audit_pack()
        
        # Verify export structure
        assert "export_metadata" in export_pack
        assert "events" in export_pack
        assert "verification" in export_pack
        
        # Verify metadata
        metadata = export_pack["export_metadata"]
        assert metadata["total_events"] == 3
        assert "export_id" in metadata
        assert "export_timestamp" in metadata
        
        # Verify events
        assert len(export_pack["events"]) == 3
        
        # Verify verification
        verification = export_pack["verification"]
        assert verification["chain_integrity_verified"] is True
        assert "export_hash" in verification
    
    def test_export_audit_pack_filtered(self):
        """Test filtered audit pack export."""
        start_date = datetime.utcnow()
        
        # Create events before filter date
        old_event = self.audit_logger.log_event(
            event_type=AuditEventType.FILE_UPLOAD,
            entity_type="SourceFile",
            entity_id="old_file",
            action="CREATE",
            description="Old file"
        )
        old_event.timestamp = start_date - timedelta(hours=1)
        
        # Create events after filter date
        for i in range(2):
            event = self.audit_logger.log_event(
                event_type=AuditEventType.RECONCILIATION_RUN,
                entity_type="ReconRun",
                entity_id=f"run_{i}",
                action="EXECUTE",
                description=f"New run {i}"
            )
            event.timestamp = start_date + timedelta(minutes=i)
        
        # Export with filters
        export_pack = self.audit_logger.export_audit_pack(
            start_date=start_date,
            entity_types=["ReconRun"],
            event_types=[AuditEventType.RECONCILIATION_RUN]
        )
        
        # Verify filtered results
        assert export_pack["export_metadata"]["total_events"] == 2
        
        # Verify all events match filters
        for event_data in export_pack["events"]:
            assert event_data["entity_type"] == "ReconRun"
            assert event_data["event_type"] == "RECONCILIATION_RUN"
            event_time = datetime.fromisoformat(event_data["timestamp"])
            assert event_time >= start_date
    
    def test_hash_calculation_consistency(self):
        """Test that hash calculation is consistent and deterministic."""
        event_data = {
            "event_id": "test_id",
            "event_type": "FILE_UPLOAD",
            "timestamp": "2024-01-01T12:00:00",
            "entity_type": "SourceFile",
            "entity_id": "file_123",
            "action": "CREATE",
            "description": "Test event"
        }
        
        # Calculate hash multiple times
        hash1 = self.audit_logger._calculate_event_hash(event_data)
        hash2 = self.audit_logger._calculate_event_hash(event_data)
        hash3 = self.audit_logger._calculate_event_hash(event_data)
        
        # Verify consistency
        assert hash1 == hash2 == hash3
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_hash_calculation_uniqueness(self):
        """Test that different events produce different hashes."""
        event_data1 = {
            "event_id": "test_id_1",
            "event_type": "FILE_UPLOAD",
            "entity_id": "file_123",
            "description": "First event"
        }
        
        event_data2 = {
            "event_id": "test_id_2",
            "event_type": "FILE_UPLOAD",
            "entity_id": "file_123",
            "description": "Second event"
        }
        
        hash1 = self.audit_logger._calculate_event_hash(event_data1)
        hash2 = self.audit_logger._calculate_event_hash(event_data2)
        
        # Verify uniqueness
        assert hash1 != hash2
    
    def test_error_handling(self):
        """Test error handling in audit logging."""
        # Test with invalid event type (should work with enum)
        event = self.audit_logger.log_event(
            event_type=AuditEventType.FILE_UPLOAD,
            entity_type="SourceFile",
            entity_id="file_123",
            action="CREATE",
            description="Test event"
        )
        
        assert event is not None
        assert event.event_type == AuditEventType.FILE_UPLOAD
    
    def test_storage_backend_integration(self):
        """Test integration with storage backend."""
        # Mock storage backend
        mock_storage = Mock()
        audit_logger = AuditLogger(storage_backend=mock_storage)
        
        # Log event
        event = audit_logger.log_event(
            event_type=AuditEventType.FILE_UPLOAD,
            entity_type="SourceFile",
            entity_id="file_123",
            action="CREATE",
            description="Test event"
        )
        
        # Verify storage backend was called
        mock_storage.store_event.assert_called_once_with(event)
    
    def test_concurrent_logging(self):
        """Test concurrent event logging (simplified)."""
        import threading
        import time
        
        events = []
        errors = []
        
        def log_events(thread_id):
            try:
                for i in range(5):
                    event = self.audit_logger.log_event(
                        event_type=AuditEventType.USER_ACTION,
                        entity_type="TestEntity",
                        entity_id=f"thread_{thread_id}_entity_{i}",
                        action="CREATE",
                        description=f"Thread {thread_id} event {i}",
                        user_id=f"user_{thread_id}"
                    )
                    events.append(event)
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Create and start threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=log_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(events) == 15  # 3 threads * 5 events
        assert len(self.audit_logger.event_chain) == 15
        
        # Verify chain integrity
        assert self.audit_logger.verify_chain_integrity() is True


class TestAuditEvent:
    """Test cases for AuditEvent dataclass."""
    
    def test_audit_event_creation(self):
        """Test AuditEvent creation and properties."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.FILE_UPLOAD,
            timestamp=timestamp,
            user_id="test_user",
            session_id="test_session",
            entity_type="SourceFile",
            entity_id="file_123",
            action="CREATE",
            severity=AuditSeverity.HIGH,
            description="Test event",
            metadata={"key": "value"},
            input_entities=["input_1"],
            output_entities=["output_1"],
            previous_hash="prev_hash",
            event_hash="event_hash",
            signature=None,
            system_version="1.0.0",
            hostname="localhost",
            process_id="proc_123"
        )
        
        # Verify all properties
        assert event.event_id == event_id
        assert event.event_type == AuditEventType.FILE_UPLOAD
        assert event.timestamp == timestamp
        assert event.user_id == "test_user"
        assert event.session_id == "test_session"
        assert event.entity_type == "SourceFile"
        assert event.entity_id == "file_123"
        assert event.action == "CREATE"
        assert event.severity == AuditSeverity.HIGH
        assert event.description == "Test event"
        assert event.metadata == {"key": "value"}
        assert event.input_entities == ["input_1"]
        assert event.output_entities == ["output_1"]
        assert event.previous_hash == "prev_hash"
        assert event.event_hash == "event_hash"
        assert event.signature is None
        assert event.system_version == "1.0.0"
        assert event.hostname == "localhost"
        assert event.process_id == "proc_123"


class TestAuditChain:
    """Test cases for AuditChain dataclass."""
    
    def test_audit_chain_creation(self):
        """Test AuditChain creation and properties."""
        chain_id = str(uuid.uuid4())
        root_event_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()
        
        # Create mock events
        events = [Mock() for _ in range(3)]
        
        chain = AuditChain(
            chain_id=chain_id,
            chain_type="test_chain",
            root_event_id=root_event_id,
            events=events,
            created_at=created_at,
            updated_at=updated_at,
            chain_hash="chain_hash_123"
        )
        
        # Verify properties
        assert chain.chain_id == chain_id
        assert chain.chain_type == "test_chain"
        assert chain.root_event_id == root_event_id
        assert chain.events == events
        assert chain.created_at == created_at
        assert chain.updated_at == updated_at
        assert chain.chain_hash == "chain_hash_123"


if __name__ == "__main__":
    pytest.main([__file__])
