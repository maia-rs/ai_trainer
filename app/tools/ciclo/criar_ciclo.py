from datetime import date

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.ciclo_service import CicloService


@tool
def criar_ciclo(usuario_id: str, nome: str, data_inicio: str) -> dict:
    """Cria um ciclo de treino para o usuario.

    Args:
        usuario_id: ID do usuário.
        nome: Nome do ciclo (ex: "Ciclo Hipertrofia Jan/2027").
        data_inicio: Data de início no formato ISO (YYYY-MM-DD).
    """
    session = SessionLocal()
    try:
        try:
            data = date.fromisoformat(data_inicio)
            ciclo_service = CicloService(session)
            ciclo = ciclo_service.criar_ciclo(usuario_id, nome, data)
            return ciclo.model_dump()
        except ValueError as e:
            return {"error": str(e)}
    finally:
        session.close()
