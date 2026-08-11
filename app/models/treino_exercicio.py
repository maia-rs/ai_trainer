from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime


class TreinoExercicio(Base):

    """ Classe de modelo para representar a relação entre treino e exercício no banco de dados. """

    __tablename__ = "treino_exercicios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    treino_id: Mapped[str] = mapped_column(String(36), nullable=False)
    exercicio_id: Mapped[str] = mapped_column(String(36), nullable=False)
    series: Mapped[int] = mapped_column(Integer, nullable=False)
    repeticoes: Mapped[int] = mapped_column(Integer, nullable=False)
    tempo_descanso: Mapped[int] = mapped_column(Integer, nullable=False)  # Tempo de descanso em segundos
    observacoes: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

