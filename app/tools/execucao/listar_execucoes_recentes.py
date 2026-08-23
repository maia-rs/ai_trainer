from datetime import datetime, timedelta, timezone

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.execucao_service import ExecucaoService
from app.service.exercicio_service import ExercicioService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService


@tool
def listar_execucoes_recentes(
    usuario_id: str,
    ultimos_dias: int = 7,
    limite: int = 20,
) -> dict:
    """Lista as execuções de treino mais recentes de um usuário.

    Parâmetros:
    - usuario_id: ID do usuário
    - ultimos_dias: quantos dias para trás buscar (padrão 7, máx 90)
    - limite: máximo de registros (padrão 20)

    Use quando o usuário perguntar:
    - "o que eu treinei essa semana?"
    - "quando foi meu último treino?"
    - "quais exercícios fiz nos últimos dias?"
    - "me mostra meu histórico recente"
    """
    session = SessionLocal()
    try:
        execucao_service = ExecucaoService(session)
        te_service = TreinoExercicioService(session)
        treino_service = TreinoService(session)
        exercicio_service = ExercicioService(session)

        dias = max(1, min(ultimos_dias, 90))
        corte = datetime.now(timezone.utc) - timedelta(days=dias)

        todas = execucao_service.listar_execucoes_por_usuario(usuario_id)

        recentes = [
            ex for ex in todas
            if (ex.data_execucao.replace(tzinfo=timezone.utc)
                if ex.data_execucao.tzinfo is None
                else ex.data_execucao) >= corte
        ]
        recentes.sort(key=lambda e: e.data_execucao, reverse=True)
        recentes = recentes[:limite]

        if not recentes:
            return {"message": f"Nenhuma execução encontrada nos últimos {dias} dias."}

        itens = []
        for ex in recentes:
            nome_exercicio = None
            nome_treino = None
            try:
                te = te_service.obter_treino_exercicio_por_id(ex.treino_exercicio_id)
                if te:
                    exercicio = exercicio_service.obter_exercicio_por_id(te.exercicio_id)
                    nome_exercicio = exercicio.nome if exercicio else None
                    treino = treino_service.obter_treino_por_id(te.treino_id)
                    nome_treino = treino.nome if treino else None
            except ValueError:
                pass

            data = ex.data_execucao
            if data.tzinfo is None:
                data = data.replace(tzinfo=timezone.utc)

            itens.append(
                {
                    "data": data.astimezone(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M"),
                    "treino": nome_treino,
                    "exercicio": nome_exercicio,
                    "carga": ex.carga,
                    "series": ex.series,
                    "repeticoes": ex.repeticoes,
                    "duracao_segundos": ex.duracao_execucao,
                    "calorias": ex.calorias_queimadas,
                    "observacoes": ex.observacoes,
                }
            )

        return {
            "periodo": f"últimos {dias} dias",
            "total": len(itens),
            "execucoes": itens,
        }

    except ValueError as e:
        return {"error": str(e)}
    finally:
        session.close()
