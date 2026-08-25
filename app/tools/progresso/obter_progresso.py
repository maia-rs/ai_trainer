from datetime import datetime, timedelta, timezone

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.avaliacao_service import AvaliacaoService
from app.service.execucao_service import ExecucaoService
from app.service.treino_exercicio import TreinoExercicioService


@tool(handle_tool_error=True)
def obter_progresso(
    usuario_id: str,
    exercicio_id: str | None = None,
    periodo_dias: int = 30,
) -> dict:
    """Retorna um resumo de progresso do usuario por periodo."""

    session = SessionLocal()

    try:
        execucao_service = ExecucaoService(session)
        treino_exercicio_service = TreinoExercicioService(session)
        avaliacao_service = AvaliacaoService(session)

        try:
            dias_considerados = max(periodo_dias, 1)
            inicio = datetime.now(timezone.utc) - timedelta(days=dias_considerados)
            execucoes = execucao_service.listar_execucoes_por_usuario(usuario_id)
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

            volume_total = sum(
                item.carga * item.repeticoes * item.series for item in execucoes
            )
            carga_media = (
                sum(item.carga for item in execucoes) / len(execucoes) if execucoes else 0
            )

            ultima_avaliacao = None
            try:
                avaliacao = avaliacao_service.obter_ultima_avaliacao_por_usuario(usuario_id)
                ultima_avaliacao = avaliacao.model_dump() if avaliacao else None
            except ValueError:
                ultima_avaliacao = None

            return {
                "periodo_dias": dias_considerados,
                "exercicio_id": exercicio_id,
                "total_execucoes": len(execucoes),
                "volume_total": volume_total,
                "carga_media": carga_media,
                "ultima_execucao": execucoes[0].model_dump() if execucoes else None,
                "ultima_avaliacao_fisica": ultima_avaliacao,
            }
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()