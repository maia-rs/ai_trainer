from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.treino_exercicio import TreinoExercicioService


@tool
def remover_exercicio_treino(treino_exercicio_id: str) -> dict:
    """Remove um exercicio de um treino."""

    session = SessionLocal()

    try:
        treino_exercicio_service = TreinoExercicioService(session)

        try:
            removido = treino_exercicio_service.deletar_treino_exercicio(treino_exercicio_id)
            if not removido:
                return {"message": "Relacao treino-exercicio nao encontrada."}
            return {"success": True}
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()