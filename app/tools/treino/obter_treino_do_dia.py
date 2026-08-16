from datetime import date, datetime

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService


_DIAS_SEMANA = [
    "Segunda-feira",
    "Terca-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sabado",
    "Domingo",
]


def _normalizar_dia_da_semana(data_referencia: date) -> str:
    return _DIAS_SEMANA[data_referencia.weekday()]


@tool
def obter_treino_do_dia(usuario_id: str, data_iso: str | None = None) -> dict:
    """Retorna o treino do dia para um usuario e seus exercicios."""

    session = SessionLocal()

    try:
        treino_service = TreinoService(session)
        treino_exercicio_service = TreinoExercicioService(session)

        try:
            if data_iso:
                data_referencia = datetime.fromisoformat(data_iso).date()
            else:
                data_referencia = datetime.now().date()

            dia_alvo = _normalizar_dia_da_semana(data_referencia)
            treinos_usuario = treino_service.listar_treinos_por_usuario(usuario_id)
            treino = next(
                (
                    item
                    for item in treinos_usuario
                    if item.status == "ativo" and item.dia_da_semana == dia_alvo
                ),
                None,
            )

            if not treino:
                return {"message": "Nenhum treino encontrado para o dia informado."}

            relacoes = treino_exercicio_service.listar_treinos_exercicios_por_treino(treino.id)
            exercicios = treino_exercicio_service.obter_exercicios_por_treino(treino.id)
            exercicios_por_id = {ex.id: ex for ex in exercicios}

            itens_treino = []
            for relacao in relacoes:
                exercicio = exercicios_por_id.get(relacao.exercicio_id)
                itens_treino.append(
                    {
                        "treino_exercicio_id": relacao.id,
                        "exercicio_id": relacao.exercicio_id,
                        "nome_exercicio": exercicio.nome if exercicio else None,
                        "series": relacao.series,
                        "repeticoes": relacao.repeticoes,
                        "descanso": relacao.descanso,
                        "observacoes": relacao.observacoes,
                    }
                )

            return {
                "treino": {
                    "id": treino.id,
                    "usuario_id": treino.usuario_id,
                    "nome": treino.nome,
                    "descricao": treino.descricao,
                    "dia_da_semana": treino.dia_da_semana,
                    "status": treino.status,
                },
                "exercicios": itens_treino,
            }
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()