from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.ciclo_service import CicloService


@tool
def obter_proxima_sessao(usuario_id: str) -> dict:
    """Retorna a proxima sessao pendente do ciclo ativo do usuario.

    Retorna None se nao houver ciclo ativo ou se todas as sessoes foram concluidas.

    Args:
        usuario_id: ID do usuário.
    """
    session = SessionLocal()
    try:
        try:
            ciclo_service = CicloService(session)
            proxima = ciclo_service.obter_proxima_sessao(usuario_id)
            return {"proxima_sessao": proxima}
        except ValueError as e:
            return {"error": str(e)}
    finally:
        session.close()
