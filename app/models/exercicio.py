from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime
from enum import Enum

class StatusExercicio(str, Enum):

    """ Enum para representar o status de um exercício. """

    ATIVO = "ativo"
    INATIVO = "inativo"

class Exercico(Base):

    """ Classe de modelo para representar um exercício no banco de dados. """
    
    __tablename__ = "exercicos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    id_externo: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    rotulo: Mapped[str] = mapped_column(String(50), nullable=False)
    grupo_muscular: Mapped[str] = mapped_column(String(50), nullable=False)
    equipamento: Mapped[str] = mapped_column(String(50), nullable=False)
    instrucoes: Mapped[str] = mapped_column(String(500), nullable=False)
    gif_url: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[StatusExercicio] = mapped_column(String(10), nullable=False, default=StatusExercicio.ATIVO.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)