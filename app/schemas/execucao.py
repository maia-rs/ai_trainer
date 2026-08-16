from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.base import AppResponseSchema


class ExecucaoCreate(BaseModel):
    """Esquema para criação de uma execução."""
    
    usuario_id: str = Field(..., description="ID do usuário associado ao exercício")
    treino_exercicio_id: str = Field(..., description="ID do treino_exercicio associado ao exercício")
    data_execucao: datetime = Field(..., description="Data de execução do exercício")
    carga: int = Field(..., description="Carga utilizada no exercício")
    series: int = Field(..., description="Número de séries realizadas no exercício")
    repeticoes: int = Field(..., description="Número de repetições realizadas no exercício")
    tempo_descanso_real: int = Field(..., description="Tempo de descanso real entre as séries do exercício (em segundos)")
    duracao_execucao: int = Field(..., description="Duração total da execução do exercício (em segundos)")
    calorias_queimadas: int = Field(..., description="Calorias queimadas durante a execução do exercício")
    frequencia_cardiaca_media: int = Field(..., description="Frequência cardíaca média durante a execução do exercício")
    observacoes: str | None = Field(None, description="Observações adicionais sobre a execução do exercício")

class ExecucaoUpdate(BaseModel):
    """Esquema para atualização de uma execução."""
    
    data_execucao: datetime | None = Field(None, description="Data de execução do exercício")
    carga: int | None = Field(None, description="Carga utilizada no exercício")
    series: int | None = Field(None, description="Número de séries realizadas no exercício")
    repeticoes: int | None = Field(None, description="Número de repetições realizadas no exercício")
    tempo_descanso_real: int | None = Field(None, description="Tempo de descanso real entre as séries do exercício (em segundos)")
    duracao_execucao: int | None = Field(None, description="Duração total da execução do exercício (em segundos)")
    calorias_queimadas: int | None = Field(None, description="Calorias queimadas durante a execução do exercício")
    frequencia_cardiaca_media: int | None = Field(None, description="Frequência cardíaca média durante a execução do exercício")
    observacoes: str | None = Field(None, description="Observações adicionais sobre a execução do exercício")

class ExecucaoResponse(AppResponseSchema):
    """Esquema para resposta de uma execução."""
    
    id: str = Field(..., description="ID da execução do exercício")
    usuario_id: str = Field(..., description="ID do usuário associado ao exercício")
    treino_exercicio_id: str = Field(..., description="ID do treino_exercicio associado ao exercício")
    data_execucao: datetime = Field(..., description="Data de execução do exercício")
    carga: int = Field(..., description="Carga utilizada no exercício")
    series: int = Field(..., description="Número de séries realizadas no exercício")
    repeticoes: int = Field(..., description="Número de repetições realizadas no exercício")
    tempo_descanso_real: int = Field(..., description="Tempo de descanso real entre as séries do exercício (em segundos)")
    duracao_execucao: int = Field(..., description="Duração total da execução do exercício (em segundos)")
    calorias_queimadas: int = Field(..., description="Calorias queimadas durante a execução do exercício")
    frequencia_cardiaca_media: int = Field(..., description="Frequência cardíaca média durante a execução do exercício")
    observacoes: str | None = Field(None, description="Observações adicionais sobre a execução do exercício")
    created_at: datetime = Field(..., description="Data de criação da execução do exercício")
    updated_at: datetime = Field(..., description="Data da última atualização da execução do exercício")