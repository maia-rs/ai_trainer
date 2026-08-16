from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.exercicio_service import ExercicioService


@tool
def buscar_informacoes_exercicio(consulta: str, limite: int = 5) -> dict:
    """Busca informacoes de exercicios no catalogo interno."""

    session = SessionLocal()

    try:
        exercicio_service = ExercicioService(session)

        try:
            limite_consulta = max(limite, 1)
            resultados = exercicio_service.search_exercicios(
                nome=consulta,
                limite=limite_consulta,
            )

            if not resultados:
                resultados = exercicio_service.search_exercicios(
                    categoria=consulta,
                    limite=limite_consulta,
                )
            if not resultados:
                resultados = exercicio_service.search_exercicios(
                    grupo_muscular=consulta,
                    limite=limite_consulta,
                )

            if not resultados:
                return {"message": "Nenhum exercicio encontrado para a consulta informada."}

            return {
                "count": len(resultados),
                "items": [
                    {
                        "id": item.id,
                        "id_externo": item.id_externo,
                        "nome": item.nome,
                        "categoria": item.categoria,
                        "grupo_muscular": item.grupo_muscular,
                        "equipamento": item.equipamento,
                        "instrucao": item.instrucao,
                        "gif_url": item.gif_url,
                    }
                    for item in resultados
                ],
            }
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()