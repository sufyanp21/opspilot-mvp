"""Data lineage tracking system for OpsPilot MVP."""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

from app.audit.audit_logger import audit_logger, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class LineageNodeType(Enum):
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


class LineageRelationType(Enum):
    """Types of relationships between lineage nodes."""
    DERIVED_FROM = "DERIVED_FROM"
    TRANSFORMED_TO = "TRANSFORMED_TO"
    GENERATED_BY = "GENERATED_BY"
    CONTAINS = "CONTAINS"
    GROUPED_INTO = "GROUPED_INTO"
    ASSIGNED_TO = "ASSIGNED_TO"
    EXPORTED_AS = "EXPORT_AS"


@dataclass
class LineageNode:
    """Represents a node in the data lineage graph."""
    node_id: str
    node_type: LineageNodeType
    entity_id: str  # ID of the actual entity (file, run, exception, etc.)
    entity_type: str  # Type name of the entity
    name: str
    description: str
    created_at: datetime
    created_by: Optional[str]
    
    # Node metadata
    metadata: Dict[str, Any]
    
    # Data characteristics
    record_count: Optional[int] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    
    # Processing information
    processing_duration: Optional[float] = None
    processing_status: str = "COMPLETED"
    error_message: Optional[str] = None


@dataclass
class LineageRelation:
    """Represents a relationship between two lineage nodes."""
    relation_id: str
    source_node_id: str
    target_node_id: str
    relation_type: LineageRelationType
    created_at: datetime
    
    # Relationship metadata
    transformation_logic: Optional[str] = None
    transformation_config: Optional[Dict[str, Any]] = None
    data_flow_metrics: Optional[Dict[str, Any]] = None


@dataclass
class LineageGraph:
    """Represents a complete lineage graph."""
    graph_id: str
    root_node_id: str
    nodes: Dict[str, LineageNode]
    relations: Dict[str, LineageRelation]
    created_at: datetime
    updated_at: datetime


class LineageTracker:
    """Tracks data lineage and transformations throughout the system."""
    
    def __init__(self):
        self.nodes: Dict[str, LineageNode] = {}
        self.relations: Dict[str, LineageRelation] = {}
        self.graphs: Dict[str, LineageGraph] = {}
    
    def create_node(
        self,
        node_type: LineageNodeType,
        entity_id: str,
        entity_type: str,
        name: str,
        description: str,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        record_count: Optional[int] = None,
        file_size: Optional[int] = None,
        checksum: Optional[str] = None
    ) -> LineageNode:
        """
        Create a new lineage node.
        
        Args:
            node_type: Type of the lineage node
            entity_id: ID of the actual entity
            entity_type: Type name of the entity
            name: Human-readable name
            description: Description of the node
            created_by: User who created the entity
            metadata: Additional metadata
            record_count: Number of records (if applicable)
            file_size: File size in bytes (if applicable)
            checksum: Data checksum (if applicable)
            
        Returns:
            Created lineage node
        """
        try:
            node_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            node = LineageNode(
                node_id=node_id,
                node_type=node_type,
                entity_id=entity_id,
                entity_type=entity_type,
                name=name,
                description=description,
                created_at=now,
                created_by=created_by,
                metadata=metadata or {},
                record_count=record_count,
                file_size=file_size,
                checksum=checksum
            )
            
            self.nodes[node_id] = node
            
            # Log audit event
            audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_ACTION,
                entity_type="LineageNode",
                entity_id=node_id,
                action="CREATE",
                description=f"Created lineage node for {entity_type}:{entity_id}",
                user_id=created_by,
                metadata={
                    "node_type": node_type.value,
                    "entity_type": entity_type,
                    "entity_id": entity_id
                }
            )
            
            logger.info(f"Created lineage node {node_id} for {entity_type}:{entity_id}")
            return node
            
        except Exception as e:
            logger.error(f"Error creating lineage node: {e}")
            raise
    
    def create_relation(
        self,
        source_node_id: str,
        target_node_id: str,
        relation_type: LineageRelationType,
        transformation_logic: Optional[str] = None,
        transformation_config: Optional[Dict[str, Any]] = None,
        data_flow_metrics: Optional[Dict[str, Any]] = None
    ) -> LineageRelation:
        """
        Create a relationship between two lineage nodes.
        
        Args:
            source_node_id: ID of the source node
            target_node_id: ID of the target node
            relation_type: Type of relationship
            transformation_logic: Description of transformation logic
            transformation_config: Configuration used for transformation
            data_flow_metrics: Metrics about the data flow
            
        Returns:
            Created lineage relation
        """
        try:
            # Validate nodes exist
            if source_node_id not in self.nodes:
                raise ValueError(f"Source node {source_node_id} not found")
            if target_node_id not in self.nodes:
                raise ValueError(f"Target node {target_node_id} not found")
            
            relation_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            relation = LineageRelation(
                relation_id=relation_id,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                relation_type=relation_type,
                created_at=now,
                transformation_logic=transformation_logic,
                transformation_config=transformation_config,
                data_flow_metrics=data_flow_metrics
            )
            
            self.relations[relation_id] = relation
            
            # Log audit event
            source_node = self.nodes[source_node_id]
            target_node = self.nodes[target_node_id]
            
            audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_ACTION,
                entity_type="LineageRelation",
                entity_id=relation_id,
                action="CREATE",
                description=f"Created {relation_type.value} relation from {source_node.name} to {target_node.name}",
                metadata={
                    "relation_type": relation_type.value,
                    "source_entity": f"{source_node.entity_type}:{source_node.entity_id}",
                    "target_entity": f"{target_node.entity_type}:{target_node.entity_id}"
                },
                input_entities=[source_node.entity_id],
                output_entities=[target_node.entity_id]
            )
            
            logger.info(f"Created lineage relation {relation_id}: {source_node.name} -> {target_node.name}")
            return relation
            
        except Exception as e:
            logger.error(f"Error creating lineage relation: {e}")
            raise
    
    def track_file_upload(
        self,
        file_id: str,
        filename: str,
        file_type: str,
        file_size: int,
        checksum: str,
        uploaded_by: str
    ) -> LineageNode:
        """Track file upload in lineage."""
        return self.create_node(
            node_type=LineageNodeType.SOURCE_FILE,
            entity_id=file_id,
            entity_type="SourceFile",
            name=filename,
            description=f"Uploaded {file_type} file: {filename}",
            created_by=uploaded_by,
            metadata={
                "file_type": file_type,
                "original_filename": filename
            },
            file_size=file_size,
            checksum=checksum
        )
    
    def track_data_parsing(
        self,
        source_file_node_id: str,
        parsed_data_id: str,
        parser_type: str,
        record_count: int,
        parsing_config: Dict[str, Any]
    ) -> Tuple[LineageNode, LineageRelation]:
        """Track data parsing operation in lineage."""
        # Create parsed data node
        parsed_node = self.create_node(
            node_type=LineageNodeType.PARSED_DATA,
            entity_id=parsed_data_id,
            entity_type="ParsedData",
            name=f"Parsed data from {self.nodes[source_file_node_id].name}",
            description=f"Data parsed using {parser_type}",
            metadata={
                "parser_type": parser_type,
                "parsing_config": parsing_config
            },
            record_count=record_count
        )
        
        # Create relation
        relation = self.create_relation(
            source_node_id=source_file_node_id,
            target_node_id=parsed_node.node_id,
            relation_type=LineageRelationType.TRANSFORMED_TO,
            transformation_logic=f"Parsed using {parser_type}",
            transformation_config=parsing_config,
            data_flow_metrics={
                "records_parsed": record_count,
                "parser_type": parser_type
            }
        )
        
        return parsed_node, relation
    
    def track_reconciliation_run(
        self,
        run_id: str,
        input_file_nodes: List[str],
        recon_config: Dict[str, Any],
        total_records: int,
        matched_records: int,
        exception_count: int
    ) -> LineageNode:
        """Track reconciliation run in lineage."""
        # Create reconciliation run node
        recon_node = self.create_node(
            node_type=LineageNodeType.RECONCILIATION_RUN,
            entity_id=run_id,
            entity_type="ReconRun",
            name=f"Reconciliation Run {run_id[:8]}",
            description="Reconciliation processing run",
            metadata={
                "recon_config": recon_config,
                "total_records": total_records,
                "matched_records": matched_records,
                "exception_count": exception_count,
                "match_rate": (matched_records / total_records * 100) if total_records > 0 else 0
            },
            record_count=total_records
        )
        
        # Create relations from input files
        for input_node_id in input_file_nodes:
            self.create_relation(
                source_node_id=input_node_id,
                target_node_id=recon_node.node_id,
                relation_type=LineageRelationType.GENERATED_BY,
                transformation_logic="Reconciliation processing",
                transformation_config=recon_config
            )
        
        return recon_node
    
    def track_exception_creation(
        self,
        exception_id: str,
        recon_run_node_id: str,
        exception_type: str,
        exception_details: Dict[str, Any]
    ) -> Tuple[LineageNode, LineageRelation]:
        """Track exception creation in lineage."""
        # Create exception node
        exception_node = self.create_node(
            node_type=LineageNodeType.EXCEPTION,
            entity_id=exception_id,
            entity_type="ReconException",
            name=f"Exception {exception_id[:8]}",
            description=f"{exception_type} exception from reconciliation",
            metadata={
                "exception_type": exception_type,
                "exception_details": exception_details
            }
        )
        
        # Create relation from reconciliation run
        relation = self.create_relation(
            source_node_id=recon_run_node_id,
            target_node_id=exception_node.node_id,
            relation_type=LineageRelationType.GENERATED_BY,
            transformation_logic="Exception identification during reconciliation"
        )
        
        return exception_node, relation
    
    def track_clustering(
        self,
        cluster_id: str,
        exception_node_ids: List[str],
        clustering_method: str,
        clustering_config: Dict[str, Any]
    ) -> LineageNode:
        """Track exception clustering in lineage."""
        # Create cluster node
        cluster_node = self.create_node(
            node_type=LineageNodeType.CLUSTER,
            entity_id=cluster_id,
            entity_type="ExceptionCluster",
            name=f"Exception Cluster {cluster_id[:8]}",
            description=f"Cluster of {len(exception_node_ids)} exceptions",
            metadata={
                "clustering_method": clustering_method,
                "clustering_config": clustering_config,
                "exception_count": len(exception_node_ids)
            },
            record_count=len(exception_node_ids)
        )
        
        # Create relations from exceptions
        for exception_node_id in exception_node_ids:
            self.create_relation(
                source_node_id=exception_node_id,
                target_node_id=cluster_node.node_id,
                relation_type=LineageRelationType.GROUPED_INTO,
                transformation_logic=f"Grouped using {clustering_method}",
                transformation_config=clustering_config
            )
        
        return cluster_node
    
    def get_upstream_lineage(self, node_id: str, max_depth: int = 10) -> List[LineageNode]:
        """Get all upstream nodes (ancestors) of a given node."""
        try:
            visited = set()
            upstream_nodes = []
            
            def traverse_upstream(current_node_id: str, depth: int):
                if depth >= max_depth or current_node_id in visited:
                    return
                
                visited.add(current_node_id)
                
                # Find all relations where this node is the target
                for relation in self.relations.values():
                    if relation.target_node_id == current_node_id:
                        source_node = self.nodes.get(relation.source_node_id)
                        if source_node and source_node not in upstream_nodes:
                            upstream_nodes.append(source_node)
                            traverse_upstream(relation.source_node_id, depth + 1)
            
            traverse_upstream(node_id, 0)
            return upstream_nodes
            
        except Exception as e:
            logger.error(f"Error getting upstream lineage: {e}")
            return []
    
    def get_downstream_lineage(self, node_id: str, max_depth: int = 10) -> List[LineageNode]:
        """Get all downstream nodes (descendants) of a given node."""
        try:
            visited = set()
            downstream_nodes = []
            
            def traverse_downstream(current_node_id: str, depth: int):
                if depth >= max_depth or current_node_id in visited:
                    return
                
                visited.add(current_node_id)
                
                # Find all relations where this node is the source
                for relation in self.relations.values():
                    if relation.source_node_id == current_node_id:
                        target_node = self.nodes.get(relation.target_node_id)
                        if target_node and target_node not in downstream_nodes:
                            downstream_nodes.append(target_node)
                            traverse_downstream(relation.target_node_id, depth + 1)
            
            traverse_downstream(node_id, 0)
            return downstream_nodes
            
        except Exception as e:
            logger.error(f"Error getting downstream lineage: {e}")
            return []
    
    def get_lineage_graph(self, root_node_id: str) -> LineageGraph:
        """Get complete lineage graph starting from a root node."""
        try:
            graph_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Get all connected nodes
            all_nodes = {}
            all_relations = {}
            
            # Start with root node
            if root_node_id in self.nodes:
                all_nodes[root_node_id] = self.nodes[root_node_id]
            
            # Get upstream and downstream
            upstream_nodes = self.get_upstream_lineage(root_node_id)
            downstream_nodes = self.get_downstream_lineage(root_node_id)
            
            # Add all connected nodes
            for node in upstream_nodes + downstream_nodes:
                all_nodes[node.node_id] = node
            
            # Add all relations between these nodes
            for relation in self.relations.values():
                if (relation.source_node_id in all_nodes and 
                    relation.target_node_id in all_nodes):
                    all_relations[relation.relation_id] = relation
            
            graph = LineageGraph(
                graph_id=graph_id,
                root_node_id=root_node_id,
                nodes=all_nodes,
                relations=all_relations,
                created_at=now,
                updated_at=now
            )
            
            self.graphs[graph_id] = graph
            
            logger.info(f"Created lineage graph {graph_id} with {len(all_nodes)} nodes and {len(all_relations)} relations")
            return graph
            
        except Exception as e:
            logger.error(f"Error creating lineage graph: {e}")
            raise
    
    def export_lineage_data(
        self,
        node_ids: Optional[List[str]] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Export lineage data for external analysis or backup."""
        try:
            export_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Filter nodes if specified
            nodes_to_export = {}
            if node_ids:
                for node_id in node_ids:
                    if node_id in self.nodes:
                        nodes_to_export[node_id] = self.nodes[node_id]
            else:
                nodes_to_export = self.nodes.copy()
            
            # Filter relations to only include those between exported nodes
            relations_to_export = {}
            for relation_id, relation in self.relations.items():
                if (relation.source_node_id in nodes_to_export and 
                    relation.target_node_id in nodes_to_export):
                    relations_to_export[relation_id] = relation
            
            export_data = {
                "export_metadata": {
                    "export_id": export_id,
                    "export_timestamp": now.isoformat(),
                    "node_count": len(nodes_to_export),
                    "relation_count": len(relations_to_export),
                    "include_metadata": include_metadata
                },
                "nodes": {},
                "relations": {}
            }
            
            # Export nodes
            for node_id, node in nodes_to_export.items():
                node_data = asdict(node)
                if not include_metadata:
                    node_data.pop("metadata", None)
                export_data["nodes"][node_id] = node_data
            
            # Export relations
            for relation_id, relation in relations_to_export.items():
                relation_data = asdict(relation)
                if not include_metadata:
                    relation_data.pop("transformation_config", None)
                    relation_data.pop("data_flow_metrics", None)
                export_data["relations"][relation_id] = relation_data
            
            logger.info(f"Exported lineage data: {len(nodes_to_export)} nodes, {len(relations_to_export)} relations")
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting lineage data: {e}")
            raise


# Global lineage tracker instance
lineage_tracker = LineageTracker()
