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
            campos: dict = {}
            if series is not None:
                campos["series"] = series
            if repeticoes is not None:
                campos["repeticoes"] = repeticoes
            if descanso is not None:
                campos["descanso"] = descanso
            if observacoes is not None:
                campos["observacoes"] = observacoes

            if not campos:
                return {"error": "Nenhum campo fornecido para atualização."}

            payload = TreinoExercicioUpdate(**campos)
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