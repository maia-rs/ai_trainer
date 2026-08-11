from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime


class Execucao(Base):
    """ Classe de modelo para representar a execução de um exercício no banco de dados. """

    __tablename__ = "execucoes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    treino_exercicio_id: Mapped[str] = mapped_column(String(36), nullable=False)
    data_execucao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    carga: Mapped[int] = mapped_column(Integer, nullable=False)  # Carga utilizada na execução
    series_realizadas: Mapped[int] = mapped_column(Integer, nullable=False)
    repeticoes_realizadas: Mapped[int] = mapped_column(Integer, nullable=False)
    tempo_descanso_real: Mapped[int] = mapped_column(Integer, nullable=False)  # Tempo de descanso em segundos
    duracao_execucao: Mapped[int] = mapped_column(Integer, nullable=False)  # Duração da execução em segundos
    calorias_queimadas: Mapped[int] = mapped_column(Integer, nullable=False)  # Calorias queimadas durante a execução
    frequencia_cardiaca_media: Mapped[int] = mapped_column(Integer, nullable=False)  # Frequência cardíaca média durante a execução
    observacoes: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)