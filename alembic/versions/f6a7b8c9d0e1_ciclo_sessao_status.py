"""ciclo_sessao_status

Substitui o campo booleano `concluido` pelo campo `status` (aguardando/em_execucao/concluida)
e adiciona `data_inicio_execucao` para rastrear quando a sessão foi iniciada.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-11-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona nova coluna status
    op.add_column(
        'ciclo_sessoes',
        sa.Column('status', sa.String(20), nullable=False, server_default='aguardando'),
    )
    # Adiciona coluna data_inicio_execucao
    op.add_column(
        'ciclo_sessoes',
        sa.Column('data_inicio_execucao', sa.DateTime(timezone=True), nullable=True),
    )
    # Migra dados: concluido=True → status='concluida'
    op.execute(
        "UPDATE ciclo_sessoes SET status = 'concluida', data_inicio_execucao = data_conclusao "
        "WHERE concluido = TRUE OR concluido = 1"
    )
    # Remove coluna antiga
    op.drop_column('ciclo_sessoes', 'concluido')


def downgrade() -> None:
    op.add_column(
        'ciclo_sessoes',
        sa.Column('concluido', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        "UPDATE ciclo_sessoes SET concluido = TRUE WHERE status = 'concluida'"
    )
    op.drop_column('ciclo_sessoes', 'data_inicio_execucao')
    op.drop_column('ciclo_sessoes', 'status')
