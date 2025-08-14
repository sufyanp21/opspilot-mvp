"""Add audit and lineage tracking tables

Revision ID: 005
Revises: 004
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM types
    audit_event_type_enum = postgresql.ENUM(
        'FILE_UPLOAD', 'RECONCILIATION_RUN', 'EXCEPTION_CREATED', 'EXCEPTION_RESOLVED',
        'EXCEPTION_ASSIGNED', 'CLUSTERING_RUN', 'SLA_BREACH', 'BULK_OPERATION',
        'DATA_EXPORT', 'CONFIGURATION_CHANGE', 'USER_ACTION', 'SYSTEM_ACTION',
        name='auditeventtypeenum'
    )
    audit_event_type_enum.create(op.get_bind())
    
    audit_severity_enum = postgresql.ENUM(
        'LOW', 'MEDIUM', 'HIGH', 'CRITICAL',
        name='auditseverityenum'
    )
    audit_severity_enum.create(op.get_bind())
    
    lineage_node_type_enum = postgresql.ENUM(
        'SOURCE_FILE', 'PARSED_DATA', 'TRANSFORMED_DATA', 'RECONCILIATION_RUN',
        'EXCEPTION', 'CLUSTER', 'ASSIGNMENT', 'REPORT', 'EXPORT',
        name='lineagenodetypeenum'
    )
    lineage_node_type_enum.create(op.get_bind())
    
    lineage_relation_type_enum = postgresql.ENUM(
        'DERIVED_FROM', 'TRANSFORMED_TO', 'GENERATED_BY', 'CONTAINS',
        'GROUPED_INTO', 'ASSIGNED_TO', 'EXPORTED_AS',
        name='lineagerelationtypeenum'
    )
    lineage_relation_type_enum.create(op.get_bind())
    
    # Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', audit_event_type_enum, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('severity', audit_severity_enum, nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('input_entities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_entities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('previous_hash', sa.String(length=64), nullable=True),
        sa.Column('event_hash', sa.String(length=64), nullable=False),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('system_version', sa.String(length=50), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=False),
        sa.Column('process_id', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id'),
        sa.UniqueConstraint('event_hash')
    )
    
    # Create indexes for audit_events
    op.create_index('idx_audit_events_entity', 'audit_events', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_events_timestamp', 'audit_events', ['timestamp'])
    op.create_index('idx_audit_events_user_timestamp', 'audit_events', ['user_id', 'timestamp'])
    op.create_index('idx_audit_events_type_timestamp', 'audit_events', ['event_type', 'timestamp'])
    op.create_index('idx_audit_events_hash_chain', 'audit_events', ['previous_hash', 'event_hash'])
    
    # Create audit_chains table
    op.create_table(
        'audit_chains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('chain_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chain_type', sa.String(length=100), nullable=False),
        sa.Column('root_event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chain_hash', sa.String(length=64), nullable=False),
        sa.Column('event_count', sa.Integer(), nullable=False),
        sa.Column('is_complete', sa.Boolean(), nullable=False),
        sa.Column('completion_timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chain_id')
    )
    
    op.create_index('idx_audit_chains_type', 'audit_chains', ['chain_type'])
    op.create_index('idx_audit_chains_root_event', 'audit_chains', ['root_event_id'])
    
    # Create lineage_nodes table
    op.create_table(
        'lineage_nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_type', lineage_node_type_enum, nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('record_count', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('processing_duration', sa.Float(), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('node_id')
    )
    
    # Create indexes for lineage_nodes
    op.create_index('idx_lineage_nodes_entity', 'lineage_nodes', ['entity_type', 'entity_id'])
    op.create_index('idx_lineage_nodes_type_created', 'lineage_nodes', ['node_type', 'created_at'])
    op.create_index('idx_lineage_nodes_created_by', 'lineage_nodes', ['created_by', 'created_at'])
    
    # Create lineage_relations table
    op.create_table(
        'lineage_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('relation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relation_type', lineage_relation_type_enum, nullable=False),
        sa.Column('transformation_logic', sa.Text(), nullable=True),
        sa.Column('transformation_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_flow_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['source_node_id'], ['lineage_nodes.node_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_node_id'], ['lineage_nodes.node_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('relation_id')
    )
    
    # Create indexes for lineage_relations
    op.create_index('idx_lineage_relations_source_target', 'lineage_relations', ['source_node_id', 'target_node_id'])
    op.create_index('idx_lineage_relations_type_created', 'lineage_relations', ['relation_type', 'created_at'])
    op.create_index('idx_lineage_relations_unique', 'lineage_relations', ['source_node_id', 'target_node_id', 'relation_type'], unique=True)
    
    # Create lineage_graphs table
    op.create_table(
        'lineage_graphs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('graph_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('root_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('graph_type', sa.String(length=100), nullable=True),
        sa.Column('node_count', sa.Integer(), nullable=False),
        sa.Column('relation_count', sa.Integer(), nullable=False),
        sa.Column('max_depth', sa.Integer(), nullable=False),
        sa.Column('graph_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('graph_hash', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['root_node_id'], ['lineage_nodes.node_id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('graph_id')
    )
    
    op.create_index('idx_lineage_graphs_type', 'lineage_graphs', ['graph_type'])
    op.create_index('idx_lineage_graphs_root', 'lineage_graphs', ['root_node_id'])
    
    # Create audit_exports table
    op.create_table(
        'audit_exports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('export_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('export_type', sa.String(length=50), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('entity_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('event_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('total_events', sa.Integer(), nullable=False),
        sa.Column('total_nodes', sa.Integer(), nullable=False),
        sa.Column('total_relations', sa.Integer(), nullable=False),
        sa.Column('export_hash', sa.String(length=64), nullable=False),
        sa.Column('chain_integrity_verified', sa.Boolean(), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('compression_type', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('export_id')
    )
    
    # Create indexes for audit_exports
    op.create_index('idx_audit_exports_type_created', 'audit_exports', ['export_type', 'created_at'])
    op.create_index('idx_audit_exports_created_by', 'audit_exports', ['created_by', 'created_at'])
    op.create_index('idx_audit_exports_date_range', 'audit_exports', ['start_date', 'end_date'])
    
    # Create audit_retention_policies table
    op.create_table(
        'audit_retention_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_name', sa.String(length=255), nullable=False),
        sa.Column('event_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('entity_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('severity_levels', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.Column('archive_after_days', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('policy_id'),
        sa.UniqueConstraint('policy_name')
    )
    
    # Create audit_archives table
    op.create_table(
        'audit_archives',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('archive_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('archive_name', sa.String(length=255), nullable=False),
        sa.Column('archive_date_start', sa.DateTime(), nullable=False),
        sa.Column('archive_date_end', sa.DateTime(), nullable=False),
        sa.Column('total_events', sa.Integer(), nullable=False),
        sa.Column('total_nodes', sa.Integer(), nullable=False),
        sa.Column('total_relations', sa.Integer(), nullable=False),
        sa.Column('storage_location', sa.String(length=1000), nullable=False),
        sa.Column('compressed_size', sa.Integer(), nullable=True),
        sa.Column('compression_ratio', sa.Float(), nullable=True),
        sa.Column('archive_hash', sa.String(length=64), nullable=False),
        sa.Column('verification_status', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('archive_id')
    )
    
    # Create indexes for audit_archives
    op.create_index('idx_audit_archives_date_range', 'audit_archives', ['archive_date_start', 'archive_date_end'])
    op.create_index('idx_audit_archives_created', 'audit_archives', ['created_at'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('audit_archives')
    op.drop_table('audit_retention_policies')
    op.drop_table('audit_exports')
    op.drop_table('lineage_graphs')
    op.drop_table('lineage_relations')
    op.drop_table('lineage_nodes')
    op.drop_table('audit_chains')
    op.drop_table('audit_events')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS lineagerelationtypeenum')
    op.execute('DROP TYPE IF EXISTS lineagenodetypeenum')
    op.execute('DROP TYPE IF EXISTS auditseverityenum')
    op.execute('DROP TYPE IF EXISTS auditeventtypeenum')
