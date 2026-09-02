"""
Retorna um resumo do treino do dia: exercícios feitos, pendentes e totais.
Útil para "o que fiz", "o que falta", "resumo do treino de hoje".
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.execucao_service import ExecucaoService
from app.service.exercicio_service import ExercicioService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService

_DIAS_SEMANA = [
    "Segunda-feira", "Terca-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sabado", "Domingo",
]

_BRT = timezone(timedelta(hours=-3))


def _dia_hoje_pt() -> str:
    return _DIAS_SEMANA[datetime.now(_BRT).weekday()]


@tool
def resumo_treino_hoje(usuario_id: str) -> dict:
    """Retorna o resumo do treino do dia: exercícios concluídos e pendentes.

    Use quando o usuário disser:
    - "o que já fiz hoje"
    - "o que falta"
    - "resumo do treino"
    - "fiz tudo hoje?"
    - "terminou o treino"
    """
    session = SessionLocal()
    try:
        treino_service = TreinoService(session)
        te_service = TreinoExercicioService(session)
        ex_service = ExercicioService(session)
        execucao_service = ExecucaoService(session)

        # Treino do dia
        treinos = treino_service.listar_treinos_por_usuario(usuario_id)
        dia_hoje = _dia_hoje_pt()

        import unicodedata
        def norm(t): return "".join(
            c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn"
        ).strip().lower()

        treino = next(
            (t for t in treinos if t.status == "ativo" and norm(t.dia_da_semana) == norm(dia_hoje)),
            None,
        )

        if not treino:
            return {"message": f"Nenhum treino ativo para hoje ({dia_hoje})."}

        relacoes = te_service.listar_treinos_exercicios_por_treino(treino.id)

        # Execuções de hoje
        inicio_hoje = datetime.now(_BRT).replace(hour=0, minute=0, second=0, microsecond=0)
        todas_exec = execucao_service.listar_execucoes_por_usuario(usuario_id)
        exec_hoje = {
            e.treino_exercicio_id
            for e in todas_exec
            if (e.data_execucao.replace(tzinfo=timezone.utc) if e.data_execucao.tzinfo is None
                else e.data_execucao).astimezone(_BRT) >= inicio_hoje
        }

        feitos = []
        pendentes = []

        for rel in relacoes:
            try:
                ex = ex_service.obter_exercicio_por_id(rel.exercicio_id)
                nome = ex.nome if ex else rel.exercicio_id
            except ValueError:
                nome = rel.exercicio_id

            item = {
                "treino_exercicio_id": rel.id,
                "nome": nome,
                "series": rel.series,
                "repeticoes": rel.repeticoes,
            }

            if rel.id in exec_hoje:
                feitos.append(item)
            else:
                pendentes.append(item)

        total = len(relacoes)
        pct = round(len(feitos) / total * 100) if total else 0

        return {
            "treino": treino.nome,
            "dia": dia_hoje,
            "total_exercicios": total,
            "concluidos": len(feitos),
            "pendentes_count": len(pendentes),
            "percentual": pct,
            "feitos": feitos,
            "pendentes": pendentes,
            "treino_completo": len(pendentes) == 0,
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()
