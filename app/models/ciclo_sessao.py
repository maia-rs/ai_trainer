from uuid import uuid4
from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class StatusCicloSessao(str, Enum):
    """Status de uma sessão de ciclo de treino."""

    AGUARDANDO = "aguardando"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDA = "concluida"


class CicloSessao(Base):
    """Classe de modelo para representar uma sessão de um ciclo de treino no banco de dados."""

    __tablename__ = "ciclo_sessoes"
    __table_args__ = (
        UniqueConstraint("ciclo_id", "numero_sessao", name="uq_ciclo_sessao"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ciclo_id: Mapped[str] = mapped_column(String(36), nullable=False)
    numero_sessao: Mapped[int] = mapped_column(Integer, nullable=False)
    treino_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=StatusCicloSessao.AGUARDANDO.value)
    data_inicio_execucao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    data_conclusao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
