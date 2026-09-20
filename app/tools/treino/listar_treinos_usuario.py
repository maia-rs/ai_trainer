from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.treino_service import TreinoService
from app.service.treino_exercicio import TreinoExercicioService


@tool
def listar_treinos_usuario(usuario_id: str) -> dict:
    """Lista todos os treinos ativos de um usuário, com os exercícios de cada um.

    Use quando o usuário perguntar:
    - "quais são meus treinos?"
    - "me mostra o treino de segunda"
    - "tenho treino hoje?"
    - "quero ver todos os meus treinos"
    """
    session = SessionLocal()
    try:
        treino_service = TreinoService(session)
        te_service = TreinoExercicioService(session)

        todos = treino_service.listar_treinos_por_usuario(usuario_id)
        ativos = [t for t in todos if t.status == "ativo"]

        if not ativos:
            return {"message": "Nenhum treino ativo encontrado."}

        resultado = []
        for treino in ativos:
            relacoes = te_service.listar_treinos_exercicios_por_treino(treino.id)
            exercicios_por_id = {
                ex.id: ex for ex in te_service.obter_exercicios_por_treino(treino.id)
            }
            exercicios = [
                {
                    "treino_exercicio_id": rel.id,
                    "exercicio_id": rel.exercicio_id,
                    "nome_exercicio": (
                        exercicios_por_id[rel.exercicio_id].nome
                        if rel.exercicio_id in exercicios_por_id
                        else None
                    ),
                    "series": rel.series,
                    "repeticoes": rel.repeticoes,
                    "descanso": rel.descanso,
                    "observacoes": rel.observacoes,
                }
                for rel in relacoes
            ]
            resultado.append(
                {
                    "id": treino.id,
                    "nome": treino.nome,
                    "descricao": treino.descricao,
                    "dia_da_semana": treino.dia_da_semana,
                    "total_exercicios": len(exercicios),
                    "exercicios": exercicios,
                }
            )

        return {"count": len(resultado), "treinos": resultado}

    except ValueError as e:
        return {"error": str(e)}
    finally:
        session.close()
