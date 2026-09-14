"""usuario meta_semanal_dias

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-09-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'b1c2d3e4f5a6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'usuarios',
        sa.Column('meta_semanal_dias', sa.Integer(), nullable=False, server_default='4')
    )


def downgrade() -> None:
    op.drop_column('usuarios', 'meta_semanal_dias')
