"""Unit tests for lineage tracker functionality."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import uuid

from app.audit.lineage_tracker import (
    LineageTracker, LineageNode, LineageRelation, LineageGraph,
    LineageNodeType, LineageRelationType
)


class TestLineageTracker:
    """Test cases for LineageTracker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lineage_tracker = LineageTracker()
        self.test_user_id = "test_user_123"
    
    def test_create_node_basic(self):
        """Test basic node creation."""
        node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.SOURCE_FILE,
            entity_id="file_123",
            entity_type="SourceFile",
            name="test_file.csv",
            description="Test CSV file",
            created_by=self.test_user_id
        )
        
        # Verify node properties
        assert node.node_type == LineageNodeType.SOURCE_FILE
        assert node.entity_id == "file_123"
        assert node.entity_type == "SourceFile"
        assert node.name == "test_file.csv"
        assert node.description == "Test CSV file"
        assert node.created_by == self.test_user_id
        assert node.node_id is not None
        assert isinstance(node.created_at, datetime)
        
        # Verify node is stored
        assert node.node_id in self.lineage_tracker.nodes
        assert self.lineage_tracker.nodes[node.node_id] == node
    
    def test_create_node_with_metadata(self):
        """Test node creation with metadata and characteristics."""
        metadata = {
            "file_type": "CSV",
            "columns": ["trade_id", "symbol", "qty"],
            "source_system": "trading_system"
        }
        
        node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="parsed_123",
            entity_type="ParsedData",
            name="Parsed trade data",
            description="Parsed CSV trade data",
            metadata=metadata,
            record_count=1000,
            file_size=50000,
            checksum="abc123def456"
        )
        
        # Verify metadata and characteristics
        assert node.metadata == metadata
        assert node.record_count == 1000
        assert node.file_size == 50000
        assert node.checksum == "abc123def456"
    
    def test_create_relation_basic(self):
        """Test basic relation creation."""
        # Create source and target nodes
        source_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.SOURCE_FILE,
            entity_id="file_123",
            entity_type="SourceFile",
            name="source_file.csv",
            description="Source file"
        )
        
        target_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="parsed_123",
            entity_type="ParsedData",
            name="Parsed data",
            description="Parsed data from source file"
        )
        
        # Create relation
        relation = self.lineage_tracker.create_relation(
            source_node_id=source_node.node_id,
            target_node_id=target_node.node_id,
            relation_type=LineageRelationType.TRANSFORMED_TO
        )
        
        # Verify relation properties
        assert relation.source_node_id == source_node.node_id
        assert relation.target_node_id == target_node.node_id
        assert relation.relation_type == LineageRelationType.TRANSFORMED_TO
        assert relation.relation_id is not None
        assert isinstance(relation.created_at, datetime)
        
        # Verify relation is stored
        assert relation.relation_id in self.lineage_tracker.relations
    
    def test_create_relation_with_transformation_details(self):
        """Test relation creation with transformation details."""
        # Create nodes
        source_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.SOURCE_FILE,
            entity_id="file_123",
            entity_type="SourceFile",
            name="source_file.csv",
            description="Source file"
        )
        
        target_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="parsed_123",
            entity_type="ParsedData",
            name="Parsed data",
            description="Parsed data"
        )
        
        transformation_config = {
            "parser": "CSV",
            "delimiter": ",",
            "encoding": "utf-8",
            "skip_rows": 1
        }
        
        data_flow_metrics = {
            "input_records": 1000,
            "output_records": 995,
            "error_records": 5,
            "processing_time": 2.5
        }
        
        # Create relation with details
        relation = self.lineage_tracker.create_relation(
            source_node_id=source_node.node_id,
            target_node_id=target_node.node_id,
            relation_type=LineageRelationType.TRANSFORMED_TO,
            transformation_logic="Parse CSV file with header row",
            transformation_config=transformation_config,
            data_flow_metrics=data_flow_metrics
        )
        
        # Verify transformation details
        assert relation.transformation_logic == "Parse CSV file with header row"
        assert relation.transformation_config == transformation_config
        assert relation.data_flow_metrics == data_flow_metrics
    
    def test_create_relation_invalid_nodes(self):
        """Test relation creation with invalid node IDs."""
        with pytest.raises(ValueError, match="Source node .* not found"):
            self.lineage_tracker.create_relation(
                source_node_id="invalid_source",
                target_node_id="invalid_target",
                relation_type=LineageRelationType.TRANSFORMED_TO
            )
    
    def test_track_file_upload(self):
        """Test file upload tracking."""
        node = self.lineage_tracker.track_file_upload(
            file_id="file_123",
            filename="trades.csv",
            file_type="CSV",
            file_size=1024,
            checksum="abc123",
            uploaded_by=self.test_user_id
        )
        
        # Verify file upload node
        assert node.node_type == LineageNodeType.SOURCE_FILE
        assert node.entity_id == "file_123"
        assert node.entity_type == "SourceFile"
        assert node.name == "trades.csv"
        assert node.created_by == self.test_user_id
        assert node.file_size == 1024
        assert node.checksum == "abc123"
        assert node.metadata["file_type"] == "CSV"
        assert node.metadata["original_filename"] == "trades.csv"
    
    def test_track_data_parsing(self):
        """Test data parsing tracking."""
        # Create source file node
        source_node = self.lineage_tracker.track_file_upload(
            file_id="file_123",
            filename="trades.csv",
            file_type="CSV",
            file_size=1024,
            checksum="abc123",
            uploaded_by=self.test_user_id
        )
        
        parsing_config = {
            "parser": "CSV",
            "delimiter": ",",
            "has_header": True
        }
        
        # Track parsing
        parsed_node, relation = self.lineage_tracker.track_data_parsing(
            source_file_node_id=source_node.node_id,
            parsed_data_id="parsed_123",
            parser_type="CSV",
            record_count=100,
            parsing_config=parsing_config
        )
        
        # Verify parsed data node
        assert parsed_node.node_type == LineageNodeType.PARSED_DATA
        assert parsed_node.entity_id == "parsed_123"
        assert parsed_node.entity_type == "ParsedData"
        assert parsed_node.record_count == 100
        assert parsed_node.metadata["parser_type"] == "CSV"
        assert parsed_node.metadata["parsing_config"] == parsing_config
        
        # Verify relation
        assert relation.source_node_id == source_node.node_id
        assert relation.target_node_id == parsed_node.node_id
        assert relation.relation_type == LineageRelationType.TRANSFORMED_TO
        assert relation.transformation_config == parsing_config
    
    def test_track_reconciliation_run(self):
        """Test reconciliation run tracking."""
        # Create input file nodes
        input_nodes = []
        for i in range(2):
            node = self.lineage_tracker.track_file_upload(
                file_id=f"file_{i}",
                filename=f"input_{i}.csv",
                file_type="CSV",
                file_size=1024,
                checksum=f"hash_{i}",
                uploaded_by=self.test_user_id
            )
            input_nodes.append(node.node_id)
        
        recon_config = {
            "match_keys": ["trade_date", "account", "symbol"],
            "price_tolerance": 0.01,
            "qty_tolerance": 0
        }
        
        # Track reconciliation run
        recon_node = self.lineage_tracker.track_reconciliation_run(
            run_id="run_123",
            input_file_nodes=input_nodes,
            recon_config=recon_config,
            total_records=1000,
            matched_records=950,
            exception_count=50
        )
        
        # Verify reconciliation node
        assert recon_node.node_type == LineageNodeType.RECONCILIATION_RUN
        assert recon_node.entity_id == "run_123"
        assert recon_node.entity_type == "ReconRun"
        assert recon_node.record_count == 1000
        assert recon_node.metadata["recon_config"] == recon_config
        assert recon_node.metadata["total_records"] == 1000
        assert recon_node.metadata["matched_records"] == 950
        assert recon_node.metadata["exception_count"] == 50
        assert recon_node.metadata["match_rate"] == 95.0
        
        # Verify relations from input files
        input_relations = [
            rel for rel in self.lineage_tracker.relations.values()
            if rel.target_node_id == recon_node.node_id
        ]
        assert len(input_relations) == 2
    
    def test_track_exception_creation(self):
        """Test exception creation tracking."""
        # Create reconciliation run node
        recon_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.RECONCILIATION_RUN,
            entity_id="run_123",
            entity_type="ReconRun",
            name="Reconciliation Run",
            description="Test reconciliation run"
        )
        
        exception_details = {
            "break_type": "PRICE_MISMATCH",
            "internal_price": 100.50,
            "cleared_price": 100.75,
            "difference": 0.25
        }
        
        # Track exception creation
        exception_node, relation = self.lineage_tracker.track_exception_creation(
            exception_id="exception_123",
            recon_run_node_id=recon_node.node_id,
            exception_type="PRICE_MISMATCH",
            exception_details=exception_details
        )
        
        # Verify exception node
        assert exception_node.node_type == LineageNodeType.EXCEPTION
        assert exception_node.entity_id == "exception_123"
        assert exception_node.entity_type == "ReconException"
        assert exception_node.metadata["exception_type"] == "PRICE_MISMATCH"
        assert exception_node.metadata["exception_details"] == exception_details
        
        # Verify relation
        assert relation.source_node_id == recon_node.node_id
        assert relation.target_node_id == exception_node.node_id
        assert relation.relation_type == LineageRelationType.GENERATED_BY
    
    def test_track_clustering(self):
        """Test exception clustering tracking."""
        # Create exception nodes
        exception_nodes = []
        for i in range(3):
            node = self.lineage_tracker.create_node(
                node_type=LineageNodeType.EXCEPTION,
                entity_id=f"exception_{i}",
                entity_type="ReconException",
                name=f"Exception {i}",
                description=f"Test exception {i}"
            )
            exception_nodes.append(node.node_id)
        
        clustering_config = {
            "method": "fuzzy_hash",
            "threshold": 0.8,
            "features": ["symbol", "account", "break_type"]
        }
        
        # Track clustering
        cluster_node = self.lineage_tracker.track_clustering(
            cluster_id="cluster_123",
            exception_node_ids=exception_nodes,
            clustering_method="fuzzy_hash",
            clustering_config=clustering_config
        )
        
        # Verify cluster node
        assert cluster_node.node_type == LineageNodeType.CLUSTER
        assert cluster_node.entity_id == "cluster_123"
        assert cluster_node.entity_type == "ExceptionCluster"
        assert cluster_node.record_count == 3
        assert cluster_node.metadata["clustering_method"] == "fuzzy_hash"
        assert cluster_node.metadata["clustering_config"] == clustering_config
        assert cluster_node.metadata["exception_count"] == 3
        
        # Verify relations from exceptions
        cluster_relations = [
            rel for rel in self.lineage_tracker.relations.values()
            if rel.target_node_id == cluster_node.node_id
        ]
        assert len(cluster_relations) == 3
        
        for relation in cluster_relations:
            assert relation.relation_type == LineageRelationType.GROUPED_INTO
            assert relation.source_node_id in exception_nodes
    
    def test_get_upstream_lineage(self):
        """Test upstream lineage retrieval."""
        # Create a chain: file -> parsed -> recon -> exception
        file_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.SOURCE_FILE,
            entity_id="file_123",
            entity_type="SourceFile",
            name="source.csv",
            description="Source file"
        )
        
        parsed_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="parsed_123",
            entity_type="ParsedData",
            name="Parsed data",
            description="Parsed data"
        )
        
        recon_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.RECONCILIATION_RUN,
            entity_id="recon_123",
            entity_type="ReconRun",
            name="Reconciliation",
            description="Reconciliation run"
        )
        
        exception_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.EXCEPTION,
            entity_id="exception_123",
            entity_type="ReconException",
            name="Exception",
            description="Reconciliation exception"
        )
        
        # Create relations
        self.lineage_tracker.create_relation(
            source_node_id=file_node.node_id,
            target_node_id=parsed_node.node_id,
            relation_type=LineageRelationType.TRANSFORMED_TO
        )
        
        self.lineage_tracker.create_relation(
            source_node_id=parsed_node.node_id,
            target_node_id=recon_node.node_id,
            relation_type=LineageRelationType.GENERATED_BY
        )
        
        self.lineage_tracker.create_relation(
            source_node_id=recon_node.node_id,
            target_node_id=exception_node.node_id,
            relation_type=LineageRelationType.GENERATED_BY
        )
        
        # Get upstream lineage for exception
        upstream = self.lineage_tracker.get_upstream_lineage(exception_node.node_id)
        
        # Verify upstream nodes
        upstream_ids = [node.node_id for node in upstream]
        assert file_node.node_id in upstream_ids
        assert parsed_node.node_id in upstream_ids
        assert recon_node.node_id in upstream_ids
        assert len(upstream) == 3
    
    def test_get_downstream_lineage(self):
        """Test downstream lineage retrieval."""
        # Create a chain: file -> parsed -> recon -> exception
        file_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.SOURCE_FILE,
            entity_id="file_123",
            entity_type="SourceFile",
            name="source.csv",
            description="Source file"
        )
        
        parsed_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="parsed_123",
            entity_type="ParsedData",
            name="Parsed data",
            description="Parsed data"
        )
        
        recon_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.RECONCILIATION_RUN,
            entity_id="recon_123",
            entity_type="ReconRun",
            name="Reconciliation",
            description="Reconciliation run"
        )
        
        exception_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.EXCEPTION,
            entity_id="exception_123",
            entity_type="ReconException",
            name="Exception",
            description="Reconciliation exception"
        )
        
        # Create relations
        self.lineage_tracker.create_relation(
            source_node_id=file_node.node_id,
            target_node_id=parsed_node.node_id,
            relation_type=LineageRelationType.TRANSFORMED_TO
        )
        
        self.lineage_tracker.create_relation(
            source_node_id=parsed_node.node_id,
            target_node_id=recon_node.node_id,
            relation_type=LineageRelationType.GENERATED_BY
        )
        
        self.lineage_tracker.create_relation(
            source_node_id=recon_node.node_id,
            target_node_id=exception_node.node_id,
            relation_type=LineageRelationType.GENERATED_BY
        )
        
        # Get downstream lineage for file
        downstream = self.lineage_tracker.get_downstream_lineage(file_node.node_id)
        
        # Verify downstream nodes
        downstream_ids = [node.node_id for node in downstream]
        assert parsed_node.node_id in downstream_ids
        assert recon_node.node_id in downstream_ids
        assert exception_node.node_id in downstream_ids
        assert len(downstream) == 3
    
    def test_get_lineage_graph(self):
        """Test complete lineage graph creation."""
        # Create a simple lineage: file -> parsed -> recon
        file_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.SOURCE_FILE,
            entity_id="file_123",
            entity_type="SourceFile",
            name="source.csv",
            description="Source file"
        )
        
        parsed_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="parsed_123",
            entity_type="ParsedData",
            name="Parsed data",
            description="Parsed data"
        )
        
        recon_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.RECONCILIATION_RUN,
            entity_id="recon_123",
            entity_type="ReconRun",
            name="Reconciliation",
            description="Reconciliation run"
        )
        
        # Create relations
        rel1 = self.lineage_tracker.create_relation(
            source_node_id=file_node.node_id,
            target_node_id=parsed_node.node_id,
            relation_type=LineageRelationType.TRANSFORMED_TO
        )
        
        rel2 = self.lineage_tracker.create_relation(
            source_node_id=parsed_node.node_id,
            target_node_id=recon_node.node_id,
            relation_type=LineageRelationType.GENERATED_BY
        )
        
        # Get lineage graph
        graph = self.lineage_tracker.get_lineage_graph(parsed_node.node_id)
        
        # Verify graph structure
        assert graph.root_node_id == parsed_node.node_id
        assert len(graph.nodes) == 3
        assert len(graph.relations) == 2
        
        # Verify nodes are included
        assert file_node.node_id in graph.nodes
        assert parsed_node.node_id in graph.nodes
        assert recon_node.node_id in graph.nodes
        
        # Verify relations are included
        assert rel1.relation_id in graph.relations
        assert rel2.relation_id in graph.relations
        
        # Verify graph is stored
        assert graph.graph_id in self.lineage_tracker.graphs
    
    def test_export_lineage_data(self):
        """Test lineage data export."""
        # Create test nodes and relations
        file_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.SOURCE_FILE,
            entity_id="file_123",
            entity_type="SourceFile",
            name="source.csv",
            description="Source file",
            metadata={"file_type": "CSV"}
        )
        
        parsed_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="parsed_123",
            entity_type="ParsedData",
            name="Parsed data",
            description="Parsed data",
            metadata={"parser": "CSV"}
        )
        
        relation = self.lineage_tracker.create_relation(
            source_node_id=file_node.node_id,
            target_node_id=parsed_node.node_id,
            relation_type=LineageRelationType.TRANSFORMED_TO,
            transformation_config={"delimiter": ","}
        )
        
        # Export all data
        export_data = self.lineage_tracker.export_lineage_data()
        
        # Verify export structure
        assert "export_metadata" in export_data
        assert "nodes" in export_data
        assert "relations" in export_data
        
        # Verify metadata
        metadata = export_data["export_metadata"]
        assert metadata["node_count"] == 2
        assert metadata["relation_count"] == 1
        assert metadata["include_metadata"] is True
        
        # Verify nodes
        assert len(export_data["nodes"]) == 2
        assert file_node.node_id in export_data["nodes"]
        assert parsed_node.node_id in export_data["nodes"]
        
        # Verify relations
        assert len(export_data["relations"]) == 1
        assert relation.relation_id in export_data["relations"]
    
    def test_export_lineage_data_filtered(self):
        """Test filtered lineage data export."""
        # Create test nodes
        file_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.SOURCE_FILE,
            entity_id="file_123",
            entity_type="SourceFile",
            name="source.csv",
            description="Source file"
        )
        
        parsed_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="parsed_123",
            entity_type="ParsedData",
            name="Parsed data",
            description="Parsed data"
        )
        
        other_node = self.lineage_tracker.create_node(
            node_type=LineageNodeType.RECONCILIATION_RUN,
            entity_id="recon_123",
            entity_type="ReconRun",
            name="Reconciliation",
            description="Reconciliation run"
        )
        
        # Export filtered data
        export_data = self.lineage_tracker.export_lineage_data(
            node_ids=[file_node.node_id, parsed_node.node_id],
            include_metadata=False
        )
        
        # Verify filtered results
        assert export_data["export_metadata"]["node_count"] == 2
        assert export_data["export_metadata"]["include_metadata"] is False
        
        # Verify only specified nodes included
        assert file_node.node_id in export_data["nodes"]
        assert parsed_node.node_id in export_data["nodes"]
        assert other_node.node_id not in export_data["nodes"]
        
        # Verify metadata excluded
        for node_data in export_data["nodes"].values():
            assert "metadata" not in node_data
    
    def test_max_depth_limiting(self):
        """Test maximum depth limiting in lineage traversal."""
        # Create a long chain
        nodes = []
        for i in range(10):
            node = self.lineage_tracker.create_node(
                node_type=LineageNodeType.PARSED_DATA,
                entity_id=f"node_{i}",
                entity_type="TestNode",
                name=f"Node {i}",
                description=f"Test node {i}"
            )
            nodes.append(node)
        
        # Create chain relations
        for i in range(9):
            self.lineage_tracker.create_relation(
                source_node_id=nodes[i].node_id,
                target_node_id=nodes[i + 1].node_id,
                relation_type=LineageRelationType.TRANSFORMED_TO
            )
        
        # Test with depth limit
        downstream = self.lineage_tracker.get_downstream_lineage(
            nodes[0].node_id, max_depth=3
        )
        
        # Should only get 3 downstream nodes (depth limited)
        assert len(downstream) == 3
        
        # Test without depth limit (default 10)
        downstream_full = self.lineage_tracker.get_downstream_lineage(
            nodes[0].node_id
        )
        
        # Should get all 9 downstream nodes
        assert len(downstream_full) == 9
    
    def test_circular_reference_handling(self):
        """Test handling of circular references in lineage."""
        # Create nodes
        node1 = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="node_1",
            entity_type="TestNode",
            name="Node 1",
            description="Test node 1"
        )
        
        node2 = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="node_2",
            entity_type="TestNode",
            name="Node 2",
            description="Test node 2"
        )
        
        node3 = self.lineage_tracker.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id="node_3",
            entity_type="TestNode",
            name="Node 3",
            description="Test node 3"
        )
        
        # Create circular relations: 1 -> 2 -> 3 -> 1
        self.lineage_tracker.create_relation(
            source_node_id=node1.node_id,
            target_node_id=node2.node_id,
            relation_type=LineageRelationType.TRANSFORMED_TO
        )
        
        self.lineage_tracker.create_relation(
            source_node_id=node2.node_id,
            target_node_id=node3.node_id,
            relation_type=LineageRelationType.TRANSFORMED_TO
        )
        
        self.lineage_tracker.create_relation(
            source_node_id=node3.node_id,
            target_node_id=node1.node_id,
            relation_type=LineageRelationType.TRANSFORMED_TO
        )
        
        # Test downstream traversal (should handle circular reference)
        downstream = self.lineage_tracker.get_downstream_lineage(node1.node_id)
        
        # Should get both other nodes without infinite loop
        assert len(downstream) == 2
        downstream_ids = [node.node_id for node in downstream]
        assert node2.node_id in downstream_ids
        assert node3.node_id in downstream_ids


if __name__ == "__main__":
    pytest.main([__file__])
