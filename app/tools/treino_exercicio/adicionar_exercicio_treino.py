from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.schemas.treino_exercicio import TreinoExercicioCreate
from app.service.treino_exercicio import TreinoExercicioService


@tool
def adicionar_exercicio_treino(
    treino_id: str,
    exercicio_id: str,
    series: int,
    repeticoes: int,
    descanso: int,
    observacoes: str | None = None,
) -> dict:
    """Adiciona um exercicio a um treino."""

    session = SessionLocal()

    try:
        treino_exercicio_service = TreinoExercicioService(session)

        try:
            payload = TreinoExercicioCreate(
                treino_id=treino_id,
                exercicio_id=exercicio_id,
                series=series,
                repeticoes=repeticoes,
                descanso=descanso,
                observacoes=observacoes,
            )
            relacao = treino_exercicio_service.criar_treino_exercicio(payload)
            return relacao.model_dump()
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()