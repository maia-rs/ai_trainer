from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

from app.tipos.telefone_tipo import TelefoneValue


def _validar_e_formatar_telefone(value: str | TelefoneValue) -> str:
    """Valida e padroniza telefone como string formatada."""
    if isinstance(value, TelefoneValue):
        return str(value)
    if isinstance(value, str):
        return str(TelefoneValue(value))
    raise TypeError("Telefone deve ser string ou TelefoneValue")

class UsuarioCreate(BaseModel):
    """Esquema para criação de um usuário."""
    
    name: str = Field(..., max_length=100, description="Nome do usuário")
    telefone: str = Field(..., max_length=15, description="Telefone do usuário no formato (XX) XXXXX-XXXX")

    @field_validator("telefone", mode="before")
    @classmethod
    def validar_telefone(cls, value: str | TelefoneValue) -> str:
        return _validar_e_formatar_telefone(value)

class UsuarioUpdate(BaseModel):
    """Esquema para atualização de um usuário."""
    
    name: str | None = Field(None, max_length=100, description="Nome do usuário")
    telefone: str | None = Field(None, max_length=15, description="Telefone do usuário no formato (XX) XXXXX-XXXX")
    status: str | None = Field(None, max_length=10, description="Status do usuário (ativo ou inativo)")

    @field_validator("telefone", mode="before")
    @classmethod
    def validar_telefone(cls, value: str | TelefoneValue | None) -> str | None:
        if value is None:
            return None
        return _validar_e_formatar_telefone(value)

class UsuarioResponse(BaseModel):
    """Esquema para resposta de um usuário."""
    
    id: str = Field(..., description="ID do usuário")
    name: str = Field(..., max_length=100, description="Nome do usuário")
    telefone: str = Field(..., max_length=15, description="Telefone do usuário no formato (XX) XXXXX-XXXX")
    status: str = Field(..., max_length=10, description="Status do usuário (ativo ou inativo)")
    created_at: str = Field(..., description="Data de criação do usuário")
    updated_at: str = Field(..., description="Data da última atualização do usuário")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("telefone", mode="before")
    @classmethod
    def validar_telefone(cls, value: str | TelefoneValue) -> str:
        return _validar_e_formatar_telefone(value)