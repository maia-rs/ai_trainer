from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


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
    concluido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_conclusao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
