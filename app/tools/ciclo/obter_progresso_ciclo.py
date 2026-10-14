from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.ciclo_service import CicloService


@tool
def obter_progresso_ciclo(ciclo_id: str) -> dict:
    """Retorna o progresso de um ciclo de treino.

    Retorna sessoes_concluidas, total_sessoes e percentual_conclusao.

    Args:
        ciclo_id: ID do ciclo.
    """
    session = SessionLocal()
    try:
        try:
            ciclo_service = CicloService(session)
            return ciclo_service.obter_progresso_ciclo(ciclo_id)
        except ValueError as e:
            return {"error": str(e)}
    finally:
        session.close()
