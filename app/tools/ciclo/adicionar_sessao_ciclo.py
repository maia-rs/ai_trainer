from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.ciclo_service import CicloService


@tool
def adicionar_sessao_ciclo(ciclo_id: str, numero_sessao: int, treino_id: str) -> dict:
    """Adiciona uma sessao a um ciclo de treino.

    Args:
        ciclo_id: ID do ciclo.
        numero_sessao: Número ordinal da sessão (começa em 1).
        treino_id: ID do treino a ser executado nessa sessão.
    """
    session = SessionLocal()
    try:
        try:
            ciclo_service = CicloService(session)
            sessao = ciclo_service.adicionar_sessao(ciclo_id, numero_sessao, treino_id)
            return sessao.model_dump()
        except ValueError as e:
            return {"error": str(e)}
    finally:
        session.close()
