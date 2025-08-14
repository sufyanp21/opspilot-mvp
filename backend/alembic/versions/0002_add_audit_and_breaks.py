from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ts_utc', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('actor_email', sa.String(length=256), nullable=True),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('object_type', sa.String(length=64), nullable=True),
        sa.Column('object_id', sa.String(length=64), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
    )

    op.create_table(
        'breaks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('severity', sa.String(length=16), nullable=False),
        sa.Column('assigned_to', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('reason_code', sa.String(length=64), nullable=True),
        sa.Column('notes', sa.JSON(), nullable=True),
        sa.Column('lineage', sa.JSON(), nullable=True),
    )
    op.create_index('ix_breaks_run_status', 'breaks', ['run_id', 'status'])
    op.create_index('ix_breaks_run_type', 'breaks', ['run_id', 'type'])

    op.create_table(
        'break_comments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('break_id', sa.Integer(), sa.ForeignKey('breaks.id', ondelete='CASCADE')),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('ts_utc', sa.DateTime(), nullable=False),
        sa.Column('text', sa.String(length=2000), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('break_comments')
    op.drop_index('ix_breaks_run_type', table_name='breaks')
    op.drop_index('ix_breaks_run_status', table_name='breaks')
    op.drop_table('breaks')
    op.drop_table('audit_log')


