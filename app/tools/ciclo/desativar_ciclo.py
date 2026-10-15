from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.ciclo_service import CicloService


@tool
def desativar_ciclo(ciclo_id: str) -> dict:
    """Desativa (pausa) um ciclo de treino ativo, liberando o usuario para criar um novo ciclo.

    Use esta tool quando o usuario quiser encerrar o ciclo atual antes de criar um novo,
    ou quando quiser pausar temporariamente o ciclo sem perder o progresso.

    Args:
        ciclo_id: ID do ciclo a ser desativado.
    """
    session = SessionLocal()
    try:
        try:
            ciclo_service = CicloService(session)
            ciclo = ciclo_service.desativar_ciclo(ciclo_id)
            return ciclo.model_dump()
        except ValueError as e:
            return {"error": str(e)}
    finally:
        session.close()
