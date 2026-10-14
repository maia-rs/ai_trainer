from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.ciclo_service import CicloService


@tool
def listar_ciclos_usuario(usuario_id: str) -> dict:
    """Lista todos os ciclos de treino de um usuario, ordenados por data de inicio decrescente.

    Args:
        usuario_id: ID do usuário.
    """
    session = SessionLocal()
    try:
        try:
            ciclo_service = CicloService(session)
            ciclos = ciclo_service.listar_ciclos_por_usuario(usuario_id)
            return {"ciclos": [c.model_dump() for c in ciclos]}
        except ValueError as e:
            return {"error": str(e)}
    finally:
        session.close()
