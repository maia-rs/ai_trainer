from uuid import uuid4
from enum import Enum
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class StatusCiclo(str, Enum):
    """Enum para representar o status de um ciclo de treino."""

    ATIVO = "ativo"
    CONCLUIDO = "concluido"
    PAUSADO = "pausado"


class Ciclo(Base):
    """Classe de modelo para representar um ciclo de treino no banco de dados."""

    __tablename__ = "ciclos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    usuario_id: Mapped[str] = mapped_column(String(36), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=StatusCiclo.ATIVO.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
