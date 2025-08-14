from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'file_registry',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source', sa.String(length=64), nullable=False),
        sa.Column('filename', sa.String(length=512), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('error', sa.String(length=2000), nullable=True),
    )
    op.create_index('ix_file_registry_sha256', 'file_registry', ['sha256'])


def downgrade() -> None:
    op.drop_index('ix_file_registry_sha256', table_name='file_registry')
    op.drop_table('file_registry')


