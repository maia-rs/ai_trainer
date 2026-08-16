from datetime import datetime, timedelta

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.progresso_service import ProgressoService


def _serializar_objeto(item):
    if item is None:
        return None
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if hasattr(item, "__dict__"):
        return {
            key: value
            for key, value in item.__dict__.items()
            if not key.startswith("_")
        }
    return item


@tool
def obter_resumo_progresso(usuario_id: str, periodo_dias: int = 30) -> dict:
    """Retorna resumo de progresso do usuario em um periodo."""

    session = SessionLocal()

    try:
        progresso_service = ProgressoService(session)

        try:
            fim = datetime.now()
            inicio = fim - timedelta(days=max(periodo_dias, 1))
            resumo = progresso_service.obter_resumo_progresso(inicio, fim)

            return {
                "usuario_id": usuario_id,
                "periodo_dias": max(periodo_dias, 1),
                "peso_evolucao": [_serializar_objeto(item) for item in resumo["peso_evolucao"]],
                "percentual_gordura_evolucao": [
                    _serializar_objeto(item) for item in resumo["percentual_gordura_evolucao"]
                ],
                "massa_muscular_evolucao": [
                    _serializar_objeto(item) for item in resumo["massa_muscular_evolucao"]
                ],
                "frequencia_treino": resumo["frequencia_treino"],
                "volume_treino": resumo["volume_treino"],
            }
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()