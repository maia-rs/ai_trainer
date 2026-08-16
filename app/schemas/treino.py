from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.base import AppResponseSchema

class TreinoCreate(BaseModel):
    """Esquema para criação de um treino."""
    
    usuario_id: str = Field(..., description="ID do usuário associado ao treino")
    nome: str = Field(..., max_length=100, description="Nome do treino")
    descricao: str = Field(..., description="Descrição detalhada do treino")
    dia_da_semana: str = Field(..., max_length=20, description="Dia da semana do treino")

class TreinoUpdate(BaseModel):
    """Esquema para atualização de um treino."""
    
    nome: str | None = Field(None, max_length=100, description="Nome do treino")
    descricao: str | None = Field(None, description="Descrição detalhada do treino")
    dia_da_semana: str | None = Field(None, max_length=20, description="Dia da semana do treino")
    status: str | None = Field(None, max_length=10, description="Status do treino (ativo ou inativo)")

class TreinoResponse(AppResponseSchema):
    """Esquema para resposta de um treino."""
    
    id: str = Field(..., description="ID do treino")
    usuario_id: str = Field(..., description="ID do usuário associado ao treino")
    nome: str = Field(..., max_length=100, description="Nome do treino")
    descricao: str = Field(..., description="Descrição detalhada do treino")
    dia_da_semana: str = Field(..., max_length=20, description="Dia da semana do treino")
    status: str = Field(..., max_length=10, description="Status do treino (ativo ou inativo)")
    created_at: datetime = Field(..., description="Data de criação do treino")
    updated_at: datetime = Field(..., description="Data da última atualização do treino")