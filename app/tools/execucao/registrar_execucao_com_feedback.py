"""
Registra execução de treino e retorna feedback de progresso comparando
com a última execução do mesmo exercício (PR, queda ou manutenção).
"""
from __future__ import annotations

from datetime import datetime, timezone

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.schemas.execucao import ExecucaoCreate
from app.service.execucao_service import ExecucaoService
from app.service.treino_exercicio import TreinoExercicioService


@tool
def registrar_execucao_com_feedback(
    usuario_id: str,
    treino_exercicio_id: str,
    carga: int,
    repeticoes: int,
    series: int,
    duracao: int = 0,
    tempo_descanso: int = 60,
    calorias_queimadas: int = 0,
    frequencia_cardiaca_media: int = 0,
    observacoes: str | None = None,
) -> dict:
    """Registra a execução de um exercício e retorna feedback de progresso.

    Use esta tool no lugar de registrar_execucao_treino quando quiser mostrar
    ao usuário se ele bateu recorde (PR), manteve ou reduziu a carga.

    Retorna:
    - dados da execução registrada
    - comparação com a última execução (delta_carga, delta_volume)
    - status: "pr" (recorde), "manteve" ou "reducao"
    """
    session = SessionLocal()
    try:
        execucao_service = ExecucaoService(session)
        te_service = TreinoExercicioService(session)

        # Busca última execução do mesmo exercício para comparação
        exercicio_id = None
        te = te_service.obter_treino_exercicio_por_id(treino_exercicio_id)
        if te:
            exercicio_id = te.exercicio_id

        ultima_carga = None
        ultimo_volume = None
        if exercicio_id:
            todas = execucao_service.listar_execucoes_por_usuario(usuario_id)
            historico = []
            for ex in todas:
                rel = te_service.obter_treino_exercicio_por_id(ex.treino_exercicio_id)
                if rel and rel.exercicio_id == exercicio_id:
                    historico.append(ex)
            if historico:
                ultima = sorted(historico, key=lambda e: e.data_execucao, reverse=True)[0]
                ultima_carga = ultima.carga
                ultimo_volume = ultima.carga * ultima.series * ultima.repeticoes

        # Registra a execução
        payload = ExecucaoCreate(
            usuario_id=usuario_id,
            treino_exercicio_id=treino_exercicio_id,
            data_execucao=datetime.now(timezone.utc),
            carga=carga,
            series=series,
            repeticoes=repeticoes,
            tempo_descanso_real=tempo_descanso,
            duracao_execucao=duracao,
            calorias_queimadas=calorias_queimadas,
            frequencia_cardiaca_media=frequencia_cardiaca_media,
            observacoes=observacoes,
        )
        execucao = execucao_service.registrar_execucao(payload)

        # Calcula feedback
        volume_atual = carga * series * repeticoes
        feedback: dict = {"status": "primeiro_registro"}

        if ultima_carga is not None:
            delta_carga = carga - ultima_carga
            delta_volume = volume_atual - (ultimo_volume or 0)

            if delta_carga > 0:
                feedback = {
                    "status": "pr",
                    "mensagem": f"🏆 Novo recorde! +{delta_carga} kg vs última execução",
                    "delta_carga": delta_carga,
                    "delta_volume": delta_volume,
                    "ultima_carga": ultima_carga,
                }
            elif delta_carga == 0:
                feedback = {
                    "status": "manteve",
                    "mensagem": f"Manteve a carga de {carga} kg",
                    "delta_carga": 0,
                    "delta_volume": delta_volume,
                    "ultima_carga": ultima_carga,
                }
            else:
                feedback = {
                    "status": "reducao",
                    "mensagem": f"Carga reduzida em {abs(delta_carga)} kg vs última execução",
                    "delta_carga": delta_carga,
                    "delta_volume": delta_volume,
                    "ultima_carga": ultima_carga,
                }

        result = execucao.model_dump()
        result["feedback"] = feedback
        return result

    except Exception as e:
        return {"status": "erro", "mensagem": f"Erro ao registrar execução: {str(e)}"}
    finally:
        session.close()
