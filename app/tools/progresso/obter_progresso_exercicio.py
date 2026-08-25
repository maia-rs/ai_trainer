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
def obter_progresso_exercicio(exercicio_id: str, periodo_dias: int = 30) -> dict:
    """Retorna progresso de um exercicio no periodo informado."""

    session = SessionLocal()

    try:
        progresso_service = ProgressoService(session)

        try:
            fim = datetime.now()
            inicio = fim - timedelta(days=max(periodo_dias, 1))
            execucoes = progresso_service.obter_exercicio_evolucao(exercicio_id, inicio, fim)

            return {
                "exercicio_id": exercicio_id,
                "periodo_dias": max(periodo_dias, 1),
                "count": len(execucoes),
                "items": [_serializar_objeto(item) for item in execucoes],
            }
        except Exception as e:
                # Captura QUALQUER exceção para sempre responder com ToolMessage
                    return {"status": "erro", "mensagem": f"Erro interno ao obter progresso do exercício: {str(e)}"}

    finally:
        session.close()