from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.schemas.treino import TreinoCreate
from app.service.treino_service import TreinoService


@tool
def criar_treino(
    usuario_id: str,
    nome: str,
    descricao: str,
    dia_da_semana: str,
) -> dict:
    """Cria um treino para um usuario."""

    session = SessionLocal()

    try:
        treino_service = TreinoService(session)

        try:
            payload = TreinoCreate(
                usuario_id=usuario_id,
                nome=nome,
                descricao=descricao,
                dia_da_semana=dia_da_semana,
            )
            treino = treino_service.criar_treino(payload)
            return treino.model_dump()
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()