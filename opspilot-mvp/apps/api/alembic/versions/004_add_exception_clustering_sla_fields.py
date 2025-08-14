"""Add exception clustering and SLA workflow fields

Revision ID: 004
Revises: 003
Create Date: 2024-08-10 14:37:31.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add clustering and SLA fields to recon_exceptions table."""
    
    # Add new enum types
    sla_severity_enum = postgresql.ENUM(
        'CRITICAL', 'HIGH', 'MEDIUM', 'LOW',
        name='slaseverity'
    )
    sla_severity_enum.create(op.get_bind())
    
    assignment_status_enum = postgresql.ENUM(
        'UNASSIGNED', 'ASSIGNED', 'IN_PROGRESS', 'ESCALATED', 'RESOLVED', 'CLOSED',
        name='assignmentstatus'
    )
    assignment_status_enum.create(op.get_bind())
    
    # Add clustering fields
    op.add_column('recon_exceptions', sa.Column('cluster_id', sa.String(255), nullable=True))
    op.add_column('recon_exceptions', sa.Column('cluster_key', sa.String(500), nullable=True))
    op.add_column('recon_exceptions', sa.Column('clustering_method', sa.String(50), nullable=True))
    op.add_column('recon_exceptions', sa.Column('cluster_confidence', sa.Float(), nullable=True))
    
    # Add SLA and workflow fields
    op.add_column('recon_exceptions', sa.Column('assignment_status', 
                                               sa.Enum('UNASSIGNED', 'ASSIGNED', 'IN_PROGRESS', 'ESCALATED', 'RESOLVED', 'CLOSED', 
                                                      name='assignmentstatus'),
                                               nullable=False, server_default='UNASSIGNED'))
    op.add_column('recon_exceptions', sa.Column('sla_severity', 
                                               sa.Enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 
                                                      name='slaseverity'),
                                               nullable=False, server_default='MEDIUM'))
    op.add_column('recon_exceptions', sa.Column('sla_due_at', sa.DateTime(), nullable=True))
    op.add_column('recon_exceptions', sa.Column('escalation_due_at', sa.DateTime(), nullable=True))
    op.add_column('recon_exceptions', sa.Column('is_sla_breached', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('recon_exceptions', sa.Column('is_escalated', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add assignment metadata fields
    op.add_column('recon_exceptions', sa.Column('assigned_team_id', sa.String(255), nullable=True))
    op.add_column('recon_exceptions', sa.Column('assignment_reason', sa.Text(), nullable=True))
    op.add_column('recon_exceptions', sa.Column('assignment_confidence', sa.Float(), nullable=True))
    op.add_column('recon_exceptions', sa.Column('manual_override', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create indexes for performance
    op.create_index('ix_recon_exceptions_cluster_id', 'recon_exceptions', ['cluster_id'])
    op.create_index('ix_recon_exceptions_assignment_status', 'recon_exceptions', ['assignment_status'])
    op.create_index('ix_recon_exceptions_sla_severity', 'recon_exceptions', ['sla_severity'])
    op.create_index('ix_recon_exceptions_sla_due_at', 'recon_exceptions', ['sla_due_at'])
    op.create_index('ix_recon_exceptions_assigned_team_id', 'recon_exceptions', ['assigned_team_id'])
    op.create_index('ix_recon_exceptions_is_sla_breached', 'recon_exceptions', ['is_sla_breached'])


def downgrade() -> None:
    """Remove clustering and SLA fields from recon_exceptions table."""
    
    # Drop indexes
    op.drop_index('ix_recon_exceptions_is_sla_breached', 'recon_exceptions')
    op.drop_index('ix_recon_exceptions_assigned_team_id', 'recon_exceptions')
    op.drop_index('ix_recon_exceptions_sla_due_at', 'recon_exceptions')
    op.drop_index('ix_recon_exceptions_sla_severity', 'recon_exceptions')
    op.drop_index('ix_recon_exceptions_assignment_status', 'recon_exceptions')
    op.drop_index('ix_recon_exceptions_cluster_id', 'recon_exceptions')
    
    # Drop assignment metadata fields
    op.drop_column('recon_exceptions', 'manual_override')
    op.drop_column('recon_exceptions', 'assignment_confidence')
    op.drop_column('recon_exceptions', 'assignment_reason')
    op.drop_column('recon_exceptions', 'assigned_team_id')
    
    # Drop SLA and workflow fields
    op.drop_column('recon_exceptions', 'is_escalated')
    op.drop_column('recon_exceptions', 'is_sla_breached')
    op.drop_column('recon_exceptions', 'escalation_due_at')
    op.drop_column('recon_exceptions', 'sla_due_at')
    op.drop_column('recon_exceptions', 'sla_severity')
    op.drop_column('recon_exceptions', 'assignment_status')
    
    # Drop clustering fields
    op.drop_column('recon_exceptions', 'cluster_confidence')
    op.drop_column('recon_exceptions', 'clustering_method')
    op.drop_column('recon_exceptions', 'cluster_key')
    op.drop_column('recon_exceptions', 'cluster_id')
    
    # Drop enum types
    assignment_status_enum = postgresql.ENUM(name='assignmentstatus')
    assignment_status_enum.drop(op.get_bind())
    
    sla_severity_enum = postgresql.ENUM(name='slaseverity')
    sla_severity_enum.drop(op.get_bind())
