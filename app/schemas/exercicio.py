from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import AppResponseSchema


class ExercicioCreate(BaseModel):
    """Esquema para criação de um exercício."""

    id_externo: str = Field(..., max_length=50, description="ID externo do exercício")
    nome: str = Field(..., max_length=100, description="Nome do exercício")
    categoria: str = Field(default="Geral", max_length=50, description="Categoria do exercício")
    rotulo: str = Field(..., max_length=100, description="Rótula do exercício")
    grupo_muscular: str = Field(..., max_length=50, description="Grupo muscular do exercício")
    equipamento: str = Field(..., max_length=50, description="Equipamento necessário para o exercício")
    instrucao: str = Field(..., description="Instrução detalhada do exercício")
    gif_url: str = Field(..., description="URL do GIF demonstrativo do exercício")


class ExercicioUpdate(BaseModel):
    """Esquema para atualização de um exercício."""

    nome: str | None = Field(None, max_length=100, description="Nome do exercício")
    categoria: str | None = Field(None, max_length=50, description="Categoria do exercício")
    rotulo: str | None = Field(None, max_length=100, description="Rótula do exercício")
    grupo_muscular: str | None = Field(None, max_length=50, description="Grupo muscular do exercício")
    equipamento: str | None = Field(None, max_length=50, description="Equipamento necessário para o exercício")
    instrucao: str | None = Field(None, description="Instrução detalhada do exercício")
    gif_url: str | None = Field(None, description="URL do GIF demonstrativo do exercício")
    status: str | None = Field(None, max_length=10, description="Status do exercício (ativo ou inativo)")


class ExercicioResponse(AppResponseSchema):
    """Esquema para resposta de um exercício."""

    id: str = Field(..., description="ID do exercício")
    id_externo: str = Field(..., max_length=50, description="ID externo do exercício")
    nome: str = Field(..., max_length=100, description="Nome do exercício")
    categoria: str = Field(..., max_length=50, description="Categoria do exercício")
    rotulo: str = Field(..., max_length=100, description="Rótula do exercício")
    grupo_muscular: str = Field(..., max_length=50, description="Grupo muscular do exercício")
    equipamento: str = Field(..., max_length=50, description="Equipamento necessário para o exercício")
    instrucao: str = Field(..., description="Instrução detalhada do exercício")
    gif_url: str = Field(..., description="URL do GIF demonstrativo do exercício")
    status: str = Field(..., max_length=10, description="Status do exercício (ativo ou inativo)")
    created_at: datetime = Field(..., description="Data de criação do exercício")
    updated_at: datetime = Field(..., description="Data da última atualização do exercício")
