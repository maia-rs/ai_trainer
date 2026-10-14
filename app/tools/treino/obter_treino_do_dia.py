from datetime import datetime

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.ciclo_service import CicloService
from app.service.treino_exercicio import TreinoExercicioService


@tool
def obter_treino_do_dia(usuario_id: str, data_iso: str | None = None) -> dict:
    """Retorna o treino do dia para um usuario e seus exercicios.

    Prioriza o ciclo ativo do usuário. Se não houver ciclo, busca pelo dia da semana.
    O campo 'fonte' indica a origem: 'ciclo' ou 'dia_semana'.
    """
    session = SessionLocal()
    try:
        ciclo_service = CicloService(session)
        treino_exercicio_service = TreinoExercicioService(session)

        try:
            resultado = ciclo_service.obter_treino_do_dia(usuario_id)

            # Se a fonte é dia_semana e data_iso foi fornecido, preserva busca por data específica
            if resultado["fonte"] == "dia_semana" and data_iso:
                data_referencia = datetime.fromisoformat(data_iso)
                treino_dia = ciclo_service.treino_service.obter_treino_do_dia_por_usuario(
                    usuario_id, data_referencia
                )
                resultado = {"fonte": "dia_semana", "treino": treino_dia}

            treino = resultado.get("treino")
            if not treino:
                return {"fonte": resultado["fonte"], "message": "Nenhum treino encontrado para hoje."}

            treino_id = treino.get("id") if isinstance(treino, dict) else treino.id

            # Enriquece com lista de exercícios
            relacoes = treino_exercicio_service.listar_treinos_exercicios_por_treino(treino_id)
            exercicios = treino_exercicio_service.obter_exercicios_por_treino(treino_id)
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

            resposta = {
                "fonte": resultado["fonte"],
                "treino": treino if isinstance(treino, dict) else {
                    "id": treino.id,
                    "usuario_id": treino.usuario_id,
                    "nome": treino.nome,
                    "descricao": treino.descricao,
                    "dia_da_semana": treino.dia_da_semana,
                    "status": treino.status,
                },
                "exercicios": itens_treino,
            }

            # Inclui ciclo_sessao_id quando a fonte é ciclo
            if resultado["fonte"] == "ciclo":
                resposta["ciclo_sessao_id"] = resultado.get("ciclo_sessao_id")

            return resposta

        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()
