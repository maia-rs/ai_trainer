from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime
from enum import Enum


class StatusTreino(str, Enum):

    """ Enum para representar o status de um treino. """

    ATIVO = "ativo"
    INATIVO = "inativo"

class Treino(Base):
    
    """ Classe de modelo para representar um treino no banco de dados. """
    
    __tablename__ = "treinos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    usuario_id: Mapped[str] = mapped_column(String(36), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(String(500), nullable=True)
    dia_da_semana: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[StatusTreino] = mapped_column(String(10), nullable=False, default=StatusTreino.ATIVO.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)