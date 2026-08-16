from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.treino_service import TreinoService


@tool
def desativar_treino(treino_id: str) -> dict:
    """Desativa um treino existente."""

    session = SessionLocal()

    try:
        treino_service = TreinoService(session)

        try:
            treino = treino_service.desativar_treino(treino_id)
            if not treino:
                return {"message": "Treino nao encontrado."}
            return treino.model_dump()
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()