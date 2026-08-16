from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.schemas.treino_exercicio import TreinoExercicioUpdate
from app.service.treino_exercicio import TreinoExercicioService


@tool
def atualizar_exercicio_treino(
    treino_exercicio_id: str,
    series: int | None = None,
    repeticoes: int | None = None,
    descanso: int | None = None,
    observacoes: str | None = None,
) -> dict:
    """Atualiza um exercicio ja vinculado ao treino."""

    session = SessionLocal()

    try:
        treino_exercicio_service = TreinoExercicioService(session)

        try:
            payload = TreinoExercicioUpdate(
                series=series,
                repeticoes=repeticoes,
                descanso=descanso,
                observacoes=observacoes,
            )
            relacao = treino_exercicio_service.atualizar_treino_exercicio(
                treino_exercicio_id,
                payload,
            )
            if not relacao:
                return {"message": "Relacao treino-exercicio nao encontrada."}
            return relacao.model_dump()
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()