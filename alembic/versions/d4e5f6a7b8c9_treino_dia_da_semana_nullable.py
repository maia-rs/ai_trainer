"""treino_dia_da_semana_nullable

Revision ID: d4e5f6a7b8c9
Revises: c2d3e4f5a6b7
Create Date: 2026-09-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c2d3e4f5a6b7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'treinos',
        'dia_da_semana',
        existing_type=sa.String(length=20),
        nullable=True,
    )


def downgrade() -> None:
    # Preenche nulos com valor placeholder antes de tornar NOT NULL
    op.execute("UPDATE treinos SET dia_da_semana = 'Sem dia' WHERE dia_da_semana IS NULL")
    op.alter_column(
        'treinos',
        'dia_da_semana',
        existing_type=sa.String(length=20),
        nullable=False,
    )
