from datetime import datetime, timezone

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.schemas.avaliacao_fisica import AvaliacaoFisicaCreate
from app.service.avaliacao_service import AvaliacaoService


@tool
def registrar_avaliacao_fisica(
    usuario_id: str,
    peso: float,
    altura: float,
    percentual_gordura: float,
    massa_gorda: float,
    massa_muscular: float,
    imc: float,
    gordura_visceral: float,
    agua_corporal: float,
    taxa_metabolica_basal: float,
    observacoes: str | None = None,
    data_avaliacao_iso: str | None = None,
) -> dict:
    """Registra uma avaliacao fisica para o usuario."""

    session = SessionLocal()

    try:
        avaliacao_service = AvaliacaoService(session)

        try:
            if data_avaliacao_iso:
                data_avaliacao = datetime.fromisoformat(data_avaliacao_iso)
            else:
                data_avaliacao = datetime.now(timezone.utc)

            payload = AvaliacaoFisicaCreate(
                usuario_id=usuario_id,
                data_avaliacao=data_avaliacao,
                peso=peso,
                altura=altura,
                percentual_gordura=percentual_gordura,
                massa_gorda=massa_gorda,
                massa_muscular=massa_muscular,
                imc=imc,
                gordura_visceral=gordura_visceral,
                agua_corporal=agua_corporal,
                taxa_metabolica_basal=taxa_metabolica_basal,
                observacoes=observacoes,
            )
            avaliacao = avaliacao_service.criar_avaliacao(payload)
            return avaliacao.model_dump()
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()