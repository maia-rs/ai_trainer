from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.progresso_service import ProgressoService


@tool
def comparar_avaliacoes_fisicas(avaliacao_id_1: str, avaliacao_id_2: str) -> dict:
    """Compara duas avaliacoes fisicas e retorna os principais indicadores."""

    session = SessionLocal()

    try:
        progresso_service = ProgressoService(session)

        try:
            comparacao = progresso_service.comparar_avaliacoes_fisicas(
                avaliacao_id_1,
                avaliacao_id_2,
            )
            return comparacao
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()