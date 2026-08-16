from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.base import AppResponseSchema

class TreinoExercicioCreate(BaseModel):
    """Esquema para criação de um treino_exercicio."""
    
    treino_id: str = Field(..., description="ID do treino associado ao treino_exercicio")
    exercicio_id: str = Field(..., description="ID do exercício associado ao treino_exercicio")
    series: int = Field(..., description="Número de séries do exercício no treino")
    repeticoes: int = Field(..., description="Número de repetições do exercício no treino")
    descanso: int = Field(..., description="Tempo de descanso entre as séries do exercício no treino (em segundos)")
    observacoes: str | None = Field(None, description="Observações adicionais sobre o treino_exercicio")

class TreinoExercicioUpdate(BaseModel):
    """Esquema para atualização de um treino_exercicio."""
    
    series: int | None = Field(None, description="Número de séries do exercício no treino")
    repeticoes: int | None = Field(None, description="Número de repetições do exercício no treino")
    descanso: int | None = Field(None, description="Tempo de descanso entre as séries do exercício no treino (em segundos)")
    observacoes: str | None = Field(None, description="Observações adicionais sobre o treino_exercicio")

class TreinoExercicioResponse(AppResponseSchema):
    """Esquema para resposta de um treino_exercicio."""
    
    id: str = Field(..., description="ID do treino_exercicio")
    treino_id: str = Field(..., description="ID do treino associado ao treino_exercicio")
    exercicio_id: str = Field(..., description="ID do exercício associado ao treino_exercicio")
    series: int = Field(..., description="Número de séries do exercício no treino")
    repeticoes: int = Field(..., description="Número de repetições do exercício no treino")
    descanso: int = Field(..., description="Tempo de descanso entre as séries do exercício no treino (em segundos)")
    observacoes: str | None = Field(None, description="Observações adicionais sobre o treino_exercicio")
    created_at: datetime = Field(..., description="Data de criação do treino_exercicio")
    updated_at: datetime = Field(..., description="Data da última atualização do treino_exercicio")