from uuid import uuid4
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime, timezone
from enum import Enum

class StatusExercicio(str, Enum):

    """ Enum para representar o status de um exercício. """

    ATIVO = "ativo"
    INATIVO = "inativo"

class Exercicio(Base):

    """ Classe de modelo para representar um exercício no banco de dados. """
    
    __tablename__ = "exercicios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    id_externo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False, default="Geral")
    rotulo: Mapped[str] = mapped_column(String(100), nullable=False)
    grupo_muscular: Mapped[str] = mapped_column(String(50), nullable=False)
    equipamento: Mapped[str] = mapped_column(String(50), nullable=False)
    instrucao: Mapped[str] = mapped_column(String(500), nullable=False)
    gif_url: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=StatusExercicio.ATIVO.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))