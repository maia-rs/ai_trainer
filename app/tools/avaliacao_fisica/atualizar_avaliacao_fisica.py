from datetime import datetime

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.schemas.avaliacao_fisica import AvaliacaoFisicaUpdate
from app.service.avaliacao_service import AvaliacaoService


@tool
def atualizar_avaliacao_fisica(
    avaliacao_id: str,
    peso: float | None = None,
    altura: float | None = None,
    percentual_gordura: float | None = None,
    massa_gorda: float | None = None,
    massa_muscular: float | None = None,
    imc: float | None = None,
    gordura_visceral: float | None = None,
    agua_corporal: float | None = None,
    taxa_metabolica_basal: float | None = None,
    observacoes: str | None = None,
    data_avaliacao_iso: str | None = None,
) -> dict:
    """Atualiza uma avaliacao fisica existente."""

    session = SessionLocal()

    try:
        avaliacao_service = AvaliacaoService(session)

        try:
            data_avaliacao = None
            if data_avaliacao_iso:
                data_avaliacao = datetime.fromisoformat(data_avaliacao_iso)

            payload = AvaliacaoFisicaUpdate(
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
            avaliacao = avaliacao_service.atualizar_avaliacao(avaliacao_id, payload)
            if not avaliacao:
                return {"message": "Avaliacao nao encontrada."}
            return avaliacao.model_dump()
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()