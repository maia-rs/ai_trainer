from datetime import datetime, timedelta, timezone

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.execucao_service import ExecucaoService
from app.service.treino_exercicio import TreinoExercicioService


@tool
def obter_historico_treino(
    usuario_id: str,
    periodo_dias: int | None = None,
    exercicio_id: str | None = None,
    limite: int = 20,
) -> dict:
    """Retorna o historico de execucoes de treino de um usuario."""

    session = SessionLocal()

    try:
        execucao_service = ExecucaoService(session)
        treino_exercicio_service = TreinoExercicioService(session)

        try:
            execucoes = execucao_service.listar_execucoes_por_usuario(usuario_id)

            if periodo_dias is not None and periodo_dias > 0:
                inicio = datetime.now(timezone.utc) - timedelta(days=periodo_dias)
                execucoes = [
                    item
                    for item in execucoes
                    if item.data_execucao.replace(tzinfo=timezone.utc) >= inicio
                ]

            if exercicio_id:
                filtradas = []
                for item in execucoes:
                    relacao = treino_exercicio_service.obter_treino_exercicio_por_id(
                        item.treino_exercicio_id
                    )
                    if relacao and relacao.exercicio_id == exercicio_id:
                        filtradas.append(item)
                execucoes = filtradas

            execucoes = sorted(execucoes, key=lambda item: item.data_execucao, reverse=True)
            execucoes = execucoes[: max(limite, 1)]

            return {
                "count": len(execucoes),
                "items": [item.model_dump() for item in execucoes],
            }
        except Exception as e:
        # Captura QUALQUER exceção para sempre responder com ToolMessage
            return {"status": "erro", "mensagem": f"Erro interno ao obter histórico de treino: {str(e)}"}

    finally:
        session.close()