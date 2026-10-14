from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.base import AppResponseSchema


class CicloCreate(BaseModel):
    """Esquema para criação de um ciclo de treino."""

    usuario_id: str = Field(..., description="ID do usuário dono do ciclo")
    nome: str = Field(..., max_length=100, description="Nome do ciclo")
    data_inicio: date = Field(..., description="Data de início do ciclo")


class CicloUpdate(BaseModel):
    """Esquema para atualização parcial de um ciclo de treino."""

    nome: str | None = Field(None, max_length=100, description="Nome do ciclo")
    status: str | None = Field(None, max_length=10, description="Status do ciclo (ativo, concluido, pausado)")


class CicloResponse(AppResponseSchema):
    """Esquema de resposta para um ciclo de treino."""

    id: str = Field(..., description="ID do ciclo")
    usuario_id: str = Field(..., description="ID do usuário dono do ciclo")
    nome: str = Field(..., description="Nome do ciclo")
    data_inicio: date = Field(..., description="Data de início do ciclo")
    status: str = Field(..., description="Status do ciclo")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")


class CicloSessaoCreate(BaseModel):
    """Esquema para criação de uma sessão de ciclo."""

    ciclo_id: str = Field(..., description="ID do ciclo ao qual a sessão pertence")
    numero_sessao: int = Field(..., ge=1, description="Número ordinal da sessão no ciclo")
    treino_id: str = Field(..., description="ID do treino associado à sessão")


class CicloSessaoResponse(AppResponseSchema):
    """Esquema de resposta para uma sessão de ciclo."""

    id: str = Field(..., description="ID da sessão")
    ciclo_id: str = Field(..., description="ID do ciclo")
    numero_sessao: int = Field(..., description="Número ordinal da sessão")
    treino_id: str = Field(..., description="ID do treino")
    concluido: bool = Field(..., description="Se a sessão foi concluída")
    data_conclusao: datetime | None = Field(None, description="Data/hora de conclusão")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")
