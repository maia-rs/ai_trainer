from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.repositorio.ciclo import CicloRepositorio
from app.repositorio.ciclo_sessao import CicloSessaoRepositorio
from app.service.ciclo_service import CicloService


@tool
def concluir_sessao(ciclo_sessao_id: str) -> dict:
    """Marca uma sessao de ciclo como concluida e retorna a proxima sessao pendente.

    Args:
        ciclo_sessao_id: ID da sessão a ser concluída.
    """
    session = SessionLocal()
    try:
        try:
            ciclo_service = CicloService(session)

            # Conclui a sessão
            sessao_concluida = ciclo_service.concluir_sessao(ciclo_sessao_id)

            # Obtém usuario_id para buscar a próxima sessão
            ciclo_repo = CicloRepositorio(session)
            sessao_repo = CicloSessaoRepositorio(session)
            sessao_obj = sessao_repo.obter_sessao_por_id(ciclo_sessao_id)
            ciclo = ciclo_repo.obter_ciclo_por_id(sessao_obj.ciclo_id) if sessao_obj else None
            usuario_id = ciclo.usuario_id if ciclo else None

            proxima = ciclo_service.obter_proxima_sessao(usuario_id) if usuario_id else None

            return {
                "sessao_concluida": sessao_concluida.model_dump(),
                "proxima_sessao": proxima,
            }
        except ValueError as e:
            return {"error": str(e)}
    finally:
        session.close()
