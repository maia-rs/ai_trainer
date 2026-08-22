from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import json
import unicodedata
from typing import Any

_BRT = ZoneInfo("America/Sao_Paulo")

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.execucao import ExecucaoCreate
from app.service.avaliacao_service import AvaliacaoService
from app.service.dashboard_token_service import DashboardTokenService
from app.service.execucao_service import ExecucaoService
from app.service.exercicio_service import ExercicioService
from app.service.progresso_service import ProgressoService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService

import os

_TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
templates = Jinja2Templates(directory=_TEMPLATES_DIR)


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


_DIAS_SEMANA = [
    "Segunda-feira",
    "Terca-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sabado",
    "Domingo",
]


def _normalizar_texto(texto: str) -> str:
    texto_sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return texto_sem_acento.strip().lower().replace("_", "-")


def _dia_semana_hoje() -> str:
    return _DIAS_SEMANA[datetime.now(_BRT).weekday()]


def _treino_do_dia_para_usuario(treinos: list[Any]) -> Any | None:
    dia_alvo = _normalizar_texto(_dia_semana_hoje())
    for treino in treinos:
        if treino.status != "ativo":
            continue
        if _normalizar_texto(treino.dia_da_semana) == dia_alvo:
            return treino
    return None


def _mapear_value_error(error: ValueError) -> HTTPException:
    mensagem = str(error)
    mensagem_norm = _normalizar_texto(mensagem)
    if "nao encontrado" in mensagem_norm:
        return HTTPException(status_code=404, detail=mensagem)
    return HTTPException(status_code=400, detail=mensagem)


def _exigir_usuario_ativo(usuario_id: str, db: Session) -> None:
    usuario = UsuarioService(db).obter_usuario_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    if usuario.status != "ativo":
        raise HTTPException(status_code=400, detail="Usuario nao esta ativo.")


def _resolver_usuario_por_token(token: str, db: Session) -> str:
    """Valida o token e retorna o usuario_id associado."""
    try:
        registro = DashboardTokenService(db).validar(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    _exigir_usuario_ativo(registro.usuario_id, db)
    return registro.usuario_id


def _treino_to_dict(treino: Any) -> dict[str, Any]:
    if treino is None:
        return {}
    return treino.model_dump(mode="json") if hasattr(treino, "model_dump") else {}


def _to_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _resumo_indicadores(
    execucoes: list[Any],
    avaliacoes: list[Any],
    periodo_dias: int = 30,
) -> dict[str, Any]:
    agora = datetime.now(timezone.utc)
    limite_periodo = agora - timedelta(days=periodo_dias)
    volume_total = sum(item.carga * item.series * item.repeticoes for item in execucoes)
    execucoes_periodo = [
        item for item in execucoes if _to_aware_utc(item.data_execucao) >= limite_periodo
    ]
    dias_treinados = {item.data_execucao.date().isoformat() for item in execucoes_periodo}

    avaliacoes_ordenadas = sorted(avaliacoes, key=lambda item: item.data_avaliacao)
    ultima = avaliacoes_ordenadas[-1] if avaliacoes_ordenadas else None
    penultima = avaliacoes_ordenadas[-2] if len(avaliacoes_ordenadas) > 1 else None

    return {
        "total_execucoes": len(execucoes),
        "total_execucoes_ultimos_30_dias": len(execucoes_periodo),
        "dias_treinados_ultimos_30_dias": len(dias_treinados),
        "volume_total": volume_total,
        "peso_atual": ultima.peso if ultima else None,
        "percentual_gordura_atual": ultima.percentual_gordura if ultima else None,
        "massa_muscular_atual": ultima.massa_muscular if ultima else None,
        "variacao_peso": (ultima.peso - penultima.peso) if ultima and penultima else None,
    }


# ---------------------------------------------------------------------------
# Helpers para preparar dados dos gráficos
# ---------------------------------------------------------------------------

def _grafico_peso(avaliacoes: list[Any]) -> dict:
    ordenadas = sorted(avaliacoes, key=lambda a: a.data_avaliacao)
    return {
        "labels": [a.data_avaliacao.strftime("%d/%m") for a in ordenadas],
        "values": [a.peso for a in ordenadas],
    }


def _grafico_composicao(avaliacoes: list[Any]) -> dict:
    ordenadas = sorted(avaliacoes, key=lambda a: a.data_avaliacao)
    return {
        "labels": [a.data_avaliacao.strftime("%d/%m") for a in ordenadas],
        "gordura": [a.percentual_gordura for a in ordenadas],
        "muscular": [a.massa_muscular for a in ordenadas],
    }


def _grafico_volume_semanal(execucoes: list[Any]) -> dict:
    semanas: dict[str, float] = defaultdict(float)
    for ex in execucoes:
        data = _to_aware_utc(ex.data_execucao)
        # ISO week: "Sem 01/2026"
        label = f"Sem {data.strftime('%W/%Y')}"
        semanas[label] += ex.carga * ex.series * ex.repeticoes
    labels = sorted(semanas.keys())
    return {
        "labels": labels,
        "values": [round(semanas[l], 1) for l in labels],
    }


def _grafico_carga_por_exercicio(
    execucoes: list[Any],
    treino_exercicio_service: TreinoExercicioService,
    exercicio_service: ExercicioService,
    max_exercicios: int = 5,
) -> dict:
    """Retorna evolução de carga máxima por exercício (últimos 90 dias)."""
    corte = datetime.now(timezone.utc) - timedelta(days=90)
    recentes = [e for e in execucoes if _to_aware_utc(e.data_execucao) >= corte]

    # agrupa por exercicio_id → data → carga máxima
    por_exercicio: dict[str, dict[str, float]] = defaultdict(dict)
    nomes: dict[str, str] = {}

    for ex in sorted(recentes, key=lambda e: e.data_execucao):
        te = treino_exercicio_service.obter_treino_exercicio_por_id(ex.treino_exercicio_id)
        if not te:
            continue
        eid = te.exercicio_id
        data_str = _to_aware_utc(ex.data_execucao).strftime("%d/%m")
        por_exercicio[eid][data_str] = max(por_exercicio[eid].get(data_str, 0), ex.carga)
        if eid not in nomes:
            try:
                nomes[eid] = exercicio_service.obter_exercicio_por_id(eid).nome
            except ValueError:
                nomes[eid] = eid

    # limita ao top N exercícios com mais registros
    top = sorted(por_exercicio.items(), key=lambda x: len(x[1]), reverse=True)[:max_exercicios]

    # eixo X unificado
    todas_datas: list[str] = sorted({d for _, datas in top for d in datas})

    datasets = [
        {
            "label": nomes.get(eid, eid),
            "data": [datas.get(d) for d in todas_datas],
        }
        for eid, datas in top
    ]

    return {"labels": todas_datas, "datasets": datasets}


# ---------------------------------------------------------------------------
# Rota de visualização HTML
# ---------------------------------------------------------------------------

@router.get("/view", response_class=HTMLResponse)
def visualizar_dashboard(
    request: Request,
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Renderiza o dashboard visual completo para o usuário autenticado via token."""
    usuario_id = _resolver_usuario_por_token(token, db)

    usuario_service = UsuarioService(db)
    treino_service = TreinoService(db)
    execucao_service = ExecucaoService(db)
    avaliacao_service = AvaliacaoService(db)
    treino_exercicio_service = TreinoExercicioService(db)
    exercicio_service = ExercicioService(db)

    usuario = usuario_service.obter_usuario_por_id(usuario_id)

    # Dados base
    treinos = treino_service.listar_treinos_por_usuario(usuario_id)
    treinos_ativos = [t for t in treinos if t.status == "ativo"]
    treino_dia = _treino_do_dia_para_usuario(treinos)

    try:
        avaliacoes = avaliacao_service.listar_avaliacoes_por_usuario(usuario_id)
    except ValueError:
        avaliacoes = []

    execucoes = execucao_service.listar_execucoes_por_usuario(usuario_id)

    indicadores = _resumo_indicadores(execucoes, avaliacoes)

    # Exercícios do treino do dia
    exercicios_dia: list[dict] = []
    if treino_dia:
        relacoes = treino_exercicio_service.listar_treinos_exercicios_por_treino(treino_dia.id)
        for ordem, rel in enumerate(relacoes, start=1):
            try:
                ex = exercicio_service.obter_exercicio_por_id(rel.exercicio_id)
                exercicios_dia.append({
                    "ordem": ordem,
                    "nome_exercicio": ex.nome,
                    "series": rel.series,
                    "repeticoes": rel.repeticoes,
                    "descanso": rel.descanso,
                    "observacoes": rel.observacoes,
                })
            except ValueError:
                continue

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "usuario_nome": usuario.name if usuario else "",
            "token": token,
            "indicadores": indicadores,
            "treino_dia": treino_dia.model_dump(mode="json") if treino_dia else None,
            "exercicios_dia": exercicios_dia,
            "treinos": [t.model_dump(mode="json") for t in treinos_ativos],
            "grafico_peso": _grafico_peso(avaliacoes),
            "grafico_composicao": _grafico_composicao(avaliacoes),
            "grafico_volume": _grafico_volume_semanal(execucoes),
            "grafico_carga": _grafico_carga_por_exercicio(
                execucoes, treino_exercicio_service, exercicio_service
            ),
        },
    )


@router.get("")
def obter_dashboard(token: str = Query(...), db: Session = Depends(get_db)) -> dict[str, Any]:
    usuario_id = _resolver_usuario_por_token(token, db)

    treino_service = TreinoService(db)
    execucao_service = ExecucaoService(db)
    avaliacao_service = AvaliacaoService(db)

    treinos = treino_service.listar_treinos_por_usuario(usuario_id)
    treinos_ativos = [item for item in treinos if item.status == "ativo"]
    treino_do_dia = _treino_do_dia_para_usuario(treinos)

    try:
        avaliacoes = avaliacao_service.listar_avaliacoes_por_usuario(usuario_id)
    except ValueError:
        avaliacoes = []

    execucoes = execucao_service.listar_execucoes_por_usuario(usuario_id)
    execucoes_ordenadas = sorted(execucoes, key=lambda item: item.data_execucao, reverse=True)

    treino_recente = None
    if execucoes_ordenadas:
        treino_exercicio_service = TreinoExercicioService(db)
        primeira_execucao = execucoes_ordenadas[0]
        treino_exercicio = treino_exercicio_service.obter_treino_exercicio_por_id(
            primeira_execucao.treino_exercicio_id
        )
        if treino_exercicio:
            treino_recente = treino_service.obter_treino_por_id(treino_exercicio.treino_id)

    try:
        ultima_avaliacao = avaliacao_service.obter_ultima_avaliacao_por_usuario(usuario_id)
    except ValueError:
        ultima_avaliacao = None

    return {
        "resumo": {
            "treino_atual": _treino_to_dict(treino_do_dia),
            "treino_recente": _treino_to_dict(treino_recente),
            "ultima_avaliacao": ultima_avaliacao.model_dump(mode="json") if ultima_avaliacao else None,
            "indicadores_principais": _resumo_indicadores(execucoes, avaliacoes),
            "total_treinos_ativos": len(treinos_ativos),
        }
    }


@router.get("/treinos")
def listar_treinos_dashboard(
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    usuario_id = _resolver_usuario_por_token(token, db)
    treino_service = TreinoService(db)

    treinos = treino_service.listar_treinos_por_usuario(usuario_id)
    ativos = [treino for treino in treinos if treino.status == "ativo"]
    return {"treinos": [treino.model_dump(mode="json") for treino in ativos]}


@router.get("/treinos/{treino_id}")
def detalhar_treino_dashboard(
    treino_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    usuario_id = _resolver_usuario_por_token(token, db)

    treino_service = TreinoService(db)
    treino_exercicio_service = TreinoExercicioService(db)
    exercicio_service = ExercicioService(db)
    execucao_service = ExecucaoService(db)

    treino = treino_service.obter_treino_por_id(treino_id)
    if not treino or treino.usuario_id != usuario_id:
        raise HTTPException(status_code=404, detail="Treino nao encontrado para este usuario.")

    relacoes = treino_exercicio_service.listar_treinos_exercicios_por_treino(treino_id)
    execucoes_usuario = execucao_service.listar_execucoes_por_usuario(usuario_id)

    exercicios_ordenados = []
    for ordem, relacao in enumerate(relacoes, start=1):
        try:
            exercicio = exercicio_service.obter_exercicio_por_id(relacao.exercicio_id)
        except ValueError as error:
            raise _mapear_value_error(error) from error

        historico_relacao = [
            item for item in execucoes_usuario if item.treino_exercicio_id == relacao.id
        ]
        historico_relacao.sort(key=lambda item: item.data_execucao, reverse=True)

        exercicios_ordenados.append(
            {
                "ordem": ordem,
                "treino_exercicio_id": relacao.id,
                "exercicio": exercicio.model_dump(mode="json"),
                "instrucoes": exercicio.instrucao,
                "series": relacao.series,
                "repeticoes": relacao.repeticoes,
                "descanso": relacao.descanso,
                "observacoes": relacao.observacoes,
                "ultima_execucao": (
                    historico_relacao[0].model_dump(mode="json") if historico_relacao else None
                ),
            }
        )

    return {
        "treino": treino.model_dump(mode="json"),
        "exercicios": exercicios_ordenados,
    }


@router.get("/treino-do-dia")
def obter_treino_do_dia_dashboard(
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    usuario_id = _resolver_usuario_por_token(token, db)

    treino_service = TreinoService(db)
    treino_exercicio_service = TreinoExercicioService(db)
    exercicio_service = ExercicioService(db)

    treinos = treino_service.listar_treinos_por_usuario(usuario_id)
    treino = _treino_do_dia_para_usuario(treinos)

    if not treino:
        return {
            "mensagem": "Nenhum treino ativo para hoje.",
            "treino": None,
            "exercicios": [],
        }

    relacoes = treino_exercicio_service.listar_treinos_exercicios_por_treino(treino.id)
    itens = []
    for ordem, relacao in enumerate(relacoes, start=1):
        try:
            exercicio = exercicio_service.obter_exercicio_por_id(relacao.exercicio_id)
        except ValueError as error:
            raise _mapear_value_error(error) from error

        itens.append(
            {
                "ordem": ordem,
                "treino_exercicio_id": relacao.id,
                "exercicio_id": relacao.exercicio_id,
                "nome_exercicio": exercicio.nome,
                "instrucoes": exercicio.instrucao,
                "series": relacao.series,
                "repeticoes": relacao.repeticoes,
                "descanso": relacao.descanso,
                "observacoes": relacao.observacoes,
            }
        )

    payload_exemplo = None
    if itens:
        payload_exemplo = ExecucaoCreate(
            usuario_id=usuario_id,
            treino_exercicio_id=itens[0]["treino_exercicio_id"],
            data_execucao=datetime.now(timezone.utc),
            carga=0,
            series=max(itens[0]["series"], 1),
            repeticoes=max(itens[0]["repeticoes"], 1),
            tempo_descanso_real=max(itens[0]["descanso"], 0),
            duracao_execucao=0,
            calorias_queimadas=0,
            frequencia_cardiaca_media=0,
            observacoes=None,
        ).model_dump(mode="json")

    return {
        "treino": treino.model_dump(mode="json"),
        "exercicios": itens,
        "registrar_execucao": {
            "disponivel": bool(itens),
            "payload_exemplo": payload_exemplo,
        },
    }


@router.get("/evolucao")
def obter_evolucao_dashboard(
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    usuario_id = _resolver_usuario_por_token(token, db)

    progresso_service = ProgressoService(db)
    execucao_service = ExecucaoService(db)
    treino_exercicio_service = TreinoExercicioService(db)
    exercicio_service = ExercicioService(db)

    execucoes = execucao_service.listar_execucoes_por_usuario(usuario_id)
    execucoes.sort(key=lambda item: item.data_execucao)

    historico_por_exercicio: dict[str, dict[str, Any]] = {}
    for execucao in execucoes:
        treino_exercicio = treino_exercicio_service.obter_treino_exercicio_por_id(execucao.treino_exercicio_id)
        if not treino_exercicio:
            continue
        exercicio_id = treino_exercicio.exercicio_id
        if exercicio_id not in historico_por_exercicio:
            try:
                exercicio = exercicio_service.obter_exercicio_por_id(exercicio_id)
            except ValueError:
                continue
            historico_por_exercicio[exercicio_id] = {
                "exercicio_id": exercicio_id,
                "nome_exercicio": exercicio.nome,
                "historico": [],
            }

        historico_por_exercicio[exercicio_id]["historico"].append(
            {
                "data_execucao": execucao.data_execucao,
                "carga": execucao.carga,
                "series": execucao.series,
                "repeticoes": execucao.repeticoes,
                "duracao_execucao": execucao.duracao_execucao,
                "tempo_descanso_real": execucao.tempo_descanso_real,
            }
        )

    data_fim = datetime.now(timezone.utc)
    data_inicio = data_fim - timedelta(days=90)

    try:
        resumo = progresso_service.obter_resumo_progresso(data_inicio=data_inicio, data_fim=data_fim)
    except ValueError as error:
        raise _mapear_value_error(error) from error

    return {
        "resumo": {
            "total_execucoes": len(execucoes),
            "volume_total": sum(item.carga * item.series * item.repeticoes for item in execucoes),
            "periodo": {
                "inicio": data_inicio,
                "fim": data_fim,
            },
        },
        "historico_por_exercicio": list(historico_por_exercicio.values()),
        "metricas_progresso": {
            "frequencia_treino": resumo["frequencia_treino"],
            "volume_treino": resumo["volume_treino"],
            "quantidade_avaliacoes": len(resumo["peso_evolucao"]),
        },
    }


@router.get("/avaliacoes")
def listar_avaliacoes_dashboard(
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    usuario_id = _resolver_usuario_por_token(token, db)

    avaliacao_service = AvaliacaoService(db)
    try:
        avaliacoes = avaliacao_service.listar_avaliacoes_por_usuario(usuario_id)
    except ValueError:
        avaliacoes = []

    avaliacoes_ordenadas = sorted(avaliacoes, key=lambda item: item.data_avaliacao)
    primeira = avaliacoes_ordenadas[0] if avaliacoes_ordenadas else None
    ultima = avaliacoes_ordenadas[-1] if avaliacoes_ordenadas else None

    return {
        "avaliacoes": [item.model_dump(mode="json") for item in avaliacoes_ordenadas],
        "evolucao_indicadores": {
            "peso": (
                (ultima.peso - primeira.peso) if primeira and ultima else None
            ),
            "percentual_gordura": (
                (ultima.percentual_gordura - primeira.percentual_gordura)
                if primeira and ultima
                else None
            ),
            "massa_muscular": (
                (ultima.massa_muscular - primeira.massa_muscular)
                if primeira and ultima
                else None
            ),
        },
    }


@router.get("/avaliacoes/{avaliacao_id}")
def detalhar_avaliacao_dashboard(
    avaliacao_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    usuario_id = _resolver_usuario_por_token(token, db)

    avaliacao_service = AvaliacaoService(db)
    try:
        avaliacao = avaliacao_service.obter_avaliacao_por_id(avaliacao_id)
    except ValueError as error:
        raise _mapear_value_error(error) from error

    if avaliacao.usuario_id != usuario_id:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada para este usuario.")

    return {"avaliacao": avaliacao.model_dump(mode="json")}