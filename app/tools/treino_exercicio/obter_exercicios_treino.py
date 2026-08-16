from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.treino_exercicio import TreinoExercicioService


@tool
def obter_exercicios_treino(treino_id: str) -> dict:
    """Retorna os exercicios vinculados a um treino."""

    session = SessionLocal()

    try:
        treino_exercicio_service = TreinoExercicioService(session)

        try:
            relacoes = treino_exercicio_service.listar_treinos_exercicios_por_treino(treino_id)
            exercicios = treino_exercicio_service.obter_exercicios_por_treino(treino_id)
            exercicios_por_id = {ex.id: ex for ex in exercicios}

            return {
                "count": len(relacoes),
                "items": [
                    {
                        "treino_exercicio_id": relacao.id,
                        "exercicio_id": relacao.exercicio_id,
                        "nome_exercicio": (
                            exercicios_por_id[relacao.exercicio_id].nome
                            if relacao.exercicio_id in exercicios_por_id
                            else None
                        ),
                        "series": relacao.series,
                        "repeticoes": relacao.repeticoes,
                        "descanso": relacao.descanso,
                        "observacoes": relacao.observacoes,
                    }
                    for relacao in relacoes
                ],
            }
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()