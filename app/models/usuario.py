from uuid import uuid4
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime, timezone
from app.tipos.telefone_tipo import Telefone, TelefoneValue
from enum import Enum # Importa o Enum do módulo padrão do Python
from sqlalchemy import Enum as SQLAlchemyEnum 
class StatusUsuario(str, Enum): 
    """ Enum para representar o status de um usuário. """
    
    ATIVO = "ativo"
    INATIVO = "inativo"
    
class Usuario(Base):

    """ Classe de modelo para representar um usuário no banco de dados. """

    __tablename__ = "usuarios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    telefone: Mapped[TelefoneValue] = mapped_column(Telefone, nullable=False) # Mapped para TelefoneValue
    status: Mapped[StatusUsuario] = mapped_column(String(10), nullable=False, default=StatusUsuario.ATIVO.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)) # Timezone-aware
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)) # Timezone-aware

    # Método __repr__ para facilitar a depuração
    def __repr__(self):
        return f"<Usuario(id='{self.id}', name='{self.name}', status='{self.status.value}')>"
