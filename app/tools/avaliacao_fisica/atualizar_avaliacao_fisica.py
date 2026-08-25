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

            # Só inclui campos que foram explicitamente fornecidos (não None)
            campos: dict = {}
            if data_avaliacao is not None:
                campos["data_avaliacao"] = data_avaliacao
            if peso is not None:
                campos["peso"] = peso
            if altura is not None:
                campos["altura"] = altura
            if percentual_gordura is not None:
                campos["percentual_gordura"] = percentual_gordura
            if massa_gorda is not None:
                campos["massa_gorda"] = massa_gorda
            if massa_muscular is not None:
                campos["massa_muscular"] = massa_muscular
            if imc is not None:
                campos["imc"] = imc
            if gordura_visceral is not None:
                campos["gordura_visceral"] = gordura_visceral
            if agua_corporal is not None:
                campos["agua_corporal"] = agua_corporal
            if taxa_metabolica_basal is not None:
                campos["taxa_metabolica_basal"] = taxa_metabolica_basal
            if observacoes is not None:
                campos["observacoes"] = observacoes

            if not campos:
                return {"error": "Nenhum campo fornecido para atualização."}

            payload = AvaliacaoFisicaUpdate(**campos)
            avaliacao = avaliacao_service.atualizar_avaliacao(avaliacao_id, payload)
            if not avaliacao:
                return {"message": "Avaliacao nao encontrada."}
            return avaliacao.model_dump()
        except Exception as e:
        # Captura QUALQUER exceção para sempre responder com ToolMessage
            return {"status": "erro", "mensagem": f"Erro interno ao atualizar avaliação: {str(e)}"}

    finally:
        session.close()