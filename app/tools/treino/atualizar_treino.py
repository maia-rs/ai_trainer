from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.schemas.treino import TreinoUpdate
from app.service.treino_service import TreinoService


@tool
def atualizar_treino(
    treino_id: str,
    nome: str | None = None,
    descricao: str | None = None,
    dia_da_semana: str | None = None,
    status: str | None = None,
) -> dict:
    """Atualiza dados de um treino."""

    session = SessionLocal()

    try:
        treino_service = TreinoService(session)

        try:
            campos: dict = {}
            if nome is not None:
                campos["nome"] = nome
            if descricao is not None:
                campos["descricao"] = descricao
            if dia_da_semana is not None:
                campos["dia_da_semana"] = dia_da_semana
            if status is not None:
                campos["status"] = status

            if not campos:
                return {"error": "Nenhum campo fornecido para atualização."}

            payload = TreinoUpdate(**campos)
            treino = treino_service.atualizar_treino(treino_id, payload)
            if not treino:
                return {"message": "Treino nao encontrado."}
            return treino.model_dump()
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()