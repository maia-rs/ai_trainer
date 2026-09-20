"""
Testes de integração — agent-resilience.

Cobrem os dois cenários mais críticos de ponta a ponta:
  B2: webhook duplicado é detectado via banco mesmo após reset do dict em memória
  B3: registrar_execucao chamado 2x com dados idênticos resulta em 1 único registro
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# B2 — Dedup de webhook via banco (integração)
# ---------------------------------------------------------------------------

import app.api.whatsapp as whatsapp_module
from app.api.whatsapp import _registrar_dedup_db, _mensagem_duplicada, _mensagens_processadas


def test_b2_webhook_deduplicado_via_banco(db_session, monkeypatch):
    """
    Fluxo completo de deduplicação via banco:
    1. Primeira chamada registra o message_id no banco → não duplicata
    2. Dict em memória é zerado (simula restart)
    3. Segunda chamada consulta o banco → detecta duplicata

    Prova que a correção do Bug 2 sobrevive a restarts de processo.
    """
    monkeypatch.setattr("app.api.whatsapp.SessionLocal", _session_factory(db_session))

    message_id = "integ-b2-webhook-001"

    # Limpa estado inicial
    _mensagens_processadas.clear()

    # Primeira chamada: deve registrar no banco e no dict
    result_1 = _mensagem_duplicada(message_id)
    assert result_1 is False, "Primeira chamada não deve ser duplicata"
    assert message_id in _mensagens_processadas

    # Simula restart: zera o dict em memória
    _mensagens_processadas.clear()
    assert message_id not in _mensagens_processadas

    # Segunda chamada: banco ainda tem o registro → deve detectar duplicata
    result_2 = _mensagem_duplicada(message_id)
    assert result_2 is True, (
        "Segunda chamada deve ser detectada como duplicata pelo banco, "
        "mesmo após o dict em memória ser zerado"
    )


def test_b2_mensagem_diferente_nao_duplicada(db_session, monkeypatch):
    """Dois message_ids distintos nunca são duplicatas entre si."""
    monkeypatch.setattr("app.api.whatsapp.SessionLocal", _session_factory(db_session))
    _mensagens_processadas.clear()

    assert _mensagem_duplicada("integ-msg-A") is False
    assert _mensagem_duplicada("integ-msg-B") is False


# ---------------------------------------------------------------------------
# B3 — Idempotência de execução via service (integração)
# ---------------------------------------------------------------------------

from app.schemas.execucao import ExecucaoCreate
from app.schemas.exercicio import ExercicioCreate
from app.schemas.treino import TreinoCreate
from app.schemas.treino_exercicio import TreinoExercicioCreate
from app.schemas.usuario import UsuarioCreate
from app.service.execucao_service import ExecucaoService
from app.service.exercicio_service import ExercicioService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService


def test_b3_registrar_execucao_idempotente(db_session):
    """
    Fluxo completo de idempotência:
    1. Cria usuário, treino, exercício e treino_exercicio
    2. Registra execução duas vezes com payload idêntico
    3. Banco deve conter exatamente 1 registro
    4. Ambas as respostas devem ter o mesmo id

    Prova que a correção do Bug 3 previne duplicatas no banco.
    """
    # Setup
    usuario = UsuarioService(db_session).criar_usuario(
        UsuarioCreate(name="Integ User B3", telefone="11930000001")
    )
    treino = TreinoService(db_session).criar_treino(
        TreinoCreate(
            usuario_id=usuario.id,
            nome="Treino Integ B3",
            descricao="Integração",
            dia_da_semana="Segunda-feira",
        )
    )
    exercicio = ExercicioService(db_session).criar_exercicio(
        ExercicioCreate(
            id_externo="integ-b3-exec",
            nome="Exercicio Integ B3",
            categoria="Forca",
            rotulo="Supino",
            grupo_muscular="Peito",
            equipamento="Barra",
            instrucao="Amplitude completa.",
            gif_url="https://example.com/integ-b3.gif",
        )
    )
    te = TreinoExercicioService(db_session).criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=4,
            repeticoes=8,
            descanso=90,
        )
    )

    payload = ExecucaoCreate(
        usuario_id=usuario.id,
        treino_exercicio_id=te.id,
        data_execucao=datetime.now(timezone.utc) - timedelta(minutes=3),
        carga=100,
        series=4,
        repeticoes=8,
        tempo_descanso_real=90,
        duracao_execucao=2400,
        calorias_queimadas=300,
        frequencia_cardiaca_media=140,
        observacoes="Integração B3",
    )

    service = ExecucaoService(db_session)

    # Duas chamadas com payload idêntico
    resp1 = service.registrar_execucao(payload)
    resp2 = service.registrar_execucao(payload)

    # Devem ter o mesmo id
    assert resp1.id == resp2.id, (
        f"IDs diferentes: {resp1.id} vs {resp2.id} — duplicata inserida"
    )

    # Banco deve ter exatamente 1 registro
    execucoes = service.listar_execucoes_por_usuario(usuario.id)
    assert len(execucoes) == 1, (
        f"Esperado 1 registro, encontrado {len(execucoes)}"
    )


# ---------------------------------------------------------------------------
# Utilitário
# ---------------------------------------------------------------------------

def _session_factory(db_session):
    """Retorna uma callable que entrega sempre a sessão de teste."""
    class _Factory:
        def __call__(self):
            return db_session
    return _Factory()
