from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'recon_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('source_set', sa.String(length=256), nullable=True),
        sa.Column('matched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('auto_tol', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('breaks_by_type', sa.JSON(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='completed'),
        sa.Column('error', sa.String(length=2000), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('recon_runs')


