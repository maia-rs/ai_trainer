from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime, timezone


class AvaliacaoFisica(Base):

    """ Classe de modelo para representar uma avaliação física no banco de dados. """

    __tablename__ = "avaliacoes_fisicas"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    usuario_id: Mapped[str] = mapped_column(String(36), nullable=False)
    data_avaliacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    peso: Mapped[float] = mapped_column(Float, nullable=False)  # Peso em kg
    altura: Mapped[float] = mapped_column(Float, nullable=False)  # Altura em cm
    percentual_gordura: Mapped[float] = mapped_column(Float, nullable=False)  # Percentual de gordura 
    massa_gorda: Mapped[float] = mapped_column(Float, nullable=False)  # Massa gorda em kg
    massa_muscular: Mapped[float] = mapped_column(Float, nullable=False)  # Massa muscular em kg
    imc: Mapped[float] = mapped_column(Float, nullable=False)  # Índice de Massa Corporal (IMC)
    gordura_visceral: Mapped[float] = mapped_column(Float, nullable=False)  # Indice de gordura visceral
    agua_corporal: Mapped[float] = mapped_column(Float, nullable=False)  # Água corporal em Litros
    taxa_metabolica_basal: Mapped[float] = mapped_column(Float, nullable=False)  # Taxa metabólica basal em kcal
    observacoes: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))