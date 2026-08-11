from pydantic import BaseModel, Field
from datetime import datetime




class AvaliacaoFisicaCreate(BaseModel):
    """Esquema para criação de uma avaliação física."""
    
    usuario_id: str = Field(..., description="ID do usuário associado à avaliação física")
    data_avaliacao: datetime = Field(..., description="Data da avaliação física")
    peso: float = Field(..., description="Peso em kg")
    altura: float = Field(..., description="Altura em cm")
    percentual_gordura: float = Field(..., description="Percentual de gordura")
    massa_gorda: float = Field(..., description="Massa gorda em kg")
    massa_muscular: float = Field(..., description="Massa muscular em kg")
    imc: float = Field(..., description="Índice de Massa Corporal (IMC)")
    gordura_visceral: float = Field(..., description="Índice de gordura visceral")
    agua_corporal: float = Field(..., description="Água corporal em Litros")
    taxa_metabolica_basal: float = Field(..., description="Taxa metabólica basal em kcal")
    observacoes: str | None = Field(None, description="Observações adicionais sobre a avaliação física")

class AvaliacaoFisicaUpdate(BaseModel):
    """Esquema para atualização de uma avaliação física."""
    
    data_avaliacao: datetime | None = Field(None, description="Data da avaliação física")
    peso: float | None = Field(None, description="Peso em kg")
    altura: float | None = Field(None, description="Altura em cm")
    percentual_gordura: float | None = Field(None, description="Percentual de gordura")
    massa_gorda: float | None = Field(None, description="Massa gorda em kg")
    massa_muscular: float | None = Field(None, description="Massa muscular em kg")
    imc: float | None = Field(None, description="Índice de Massa Corporal (IMC)")
    gordura_visceral: float | None = Field(None, description="Índice de gordura visceral")
    agua_corporal: float | None = Field(None, description="Água corporal em Litros")
    taxa_metabolica_basal: float | None = Field(None, description="Taxa metabólica basal em kcal")
    observacoes: str | None = Field(None, description="Observações adicionais sobre a avaliação física")

class AvaliacaoFisicaResponse(BaseModel):
    """Esquema para resposta de uma avaliação física."""
    
    id: str = Field(..., description="ID da avaliação física")
    usuario_id: str = Field(..., description="ID do usuário associado à avaliação física")
    data_avaliacao: datetime = Field(..., description="Data da avaliação física")
    peso: float = Field(..., description="Peso em kg")
    altura: float = Field(..., description="Altura em cm")
    percentual_gordura: float = Field(..., description="Percentual de gordura")
    massa_gorda: float = Field(..., description="Massa gorda em kg")
    massa_muscular: float = Field(..., description="Massa muscular em kg")
    imc: float = Field(..., description="Índice de Massa Corporal (IMC)")
    gordura_visceral: float = Field(..., description="Índice de gordura visceral")
    agua_corporal: float = Field(..., description="Água corporal em Litros")
    taxa_metabolica_basal: float = Field(..., description="Taxa metabólica basal em kcal")
    observacoes: str | None = Field(None, description="Observações adicionais sobre a avaliação física")
    created_at: datetime = Field(..., description="Data de criação da avaliação física") # Alterado de str para datetime
    updated_at: datetime = Field(..., description="Data da última atualização da avaliação física") # Alterado de str para datetime

    class Config:
        orm_mode = True