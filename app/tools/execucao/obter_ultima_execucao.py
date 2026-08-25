from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.execucao_service import ExecucaoService
from app.service.treino_exercicio import TreinoExercicioService


@tool
def obter_ultima_execucao(usuario_id: str, exercicio_id: str | None = None) -> dict:
    """Retorna a ultima execucao de treino do usuario."""

    session = SessionLocal()

    try:
        execucao_service = ExecucaoService(session)
        treino_exercicio_service = TreinoExercicioService(session)

        try:
            execucoes = execucao_service.listar_execucoes_por_usuario(usuario_id)

            if exercicio_id:
                filtradas = []
                for item in execucoes:
                    relacao = treino_exercicio_service.obter_treino_exercicio_por_id(
                        item.treino_exercicio_id
                    )
                    if relacao and relacao.exercicio_id == exercicio_id:
                        filtradas.append(item)
                execucoes = filtradas

            if not execucoes:
                return {"message": "Nenhuma execucao encontrada."}

            ultima = sorted(execucoes, key=lambda item: item.data_execucao, reverse=True)[0]
            return ultima.model_dump()
        except Exception as e:
            # Captura QUALQUER exceção para sempre responder com ToolMessage
            return {"status": "erro", "mensagem": f"Erro interno ao obter última execução: {str(e)}"}

    finally:
        session.close()