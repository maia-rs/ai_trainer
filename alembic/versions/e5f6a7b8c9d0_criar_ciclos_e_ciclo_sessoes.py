"""criar_ciclos_e_ciclo_sessoes

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ciclos',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('usuario_id', sa.String(36), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('data_inicio', sa.Date(), nullable=False),
        sa.Column('status', sa.String(10), nullable=False, server_default='ativo'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'ciclo_sessoes',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('ciclo_id', sa.String(36), sa.ForeignKey('ciclos.id'), nullable=False),
        sa.Column('numero_sessao', sa.Integer(), nullable=False),
        sa.Column('treino_id', sa.String(36), sa.ForeignKey('treinos.id'), nullable=False),
        sa.Column('concluido', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('data_conclusao', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('ciclo_id', 'numero_sessao', name='uq_ciclo_sessao'),
    )


def downgrade() -> None:
    op.drop_table('ciclo_sessoes')
    op.drop_table('ciclos')
