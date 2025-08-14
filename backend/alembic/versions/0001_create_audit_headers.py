from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'audit_headers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('time', sa.DateTime(), nullable=False),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('correlation_id', sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('audit_headers')


