"""
Testes exploratórios pré-fix para os 4 bugs de resiliência do AITrainer.

Estes testes são ESPERADOS PARA FALHAR no código atual — cada falha
confirma que o bug existe. Após os fixes (Tasks 2-5), eles devem passar.

B1 — MemorySaver volátil: checkpointer usa RAM (perde estado em restarts)
B2 — Dedup em RAM: _mensagens_processadas zerado em restart → duplicata processada
B3 — Sem idempotência: registrar_execucao 2x com payload idêntico insere 2 registros
B4 — HTTP sem retry: RequestError capturado imediatamente, httpx.post chamado 1x
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call

import httpx
import pytest

# ---------------------------------------------------------------------------
# Helpers de fixture — padrão usado nos outros testes de service
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
from app.service import agente_service as agente_module
from app.service.whatsapp_service import WhatsappService


def _criar_usuario(db_session, nome: str, telefone: str):
    return UsuarioService(db_session).criar_usuario(
        UsuarioCreate(name=nome, telefone=telefone)
    )


def _criar_treino(db_session, usuario_id: str):
    return TreinoService(db_session).criar_treino(
        TreinoCreate(
            usuario_id=usuario_id,
            nome="Treino Exploratorio",
            descricao="Treino para testes exploratórios",
            dia_da_semana="Segunda-feira",
        )
    )


def _criar_exercicio(db_session, sufixo: str = "exp"):
    return ExercicioService(db_session).criar_exercicio(
        ExercicioCreate(
            id_externo=f"exp-{sufixo}",
            nome=f"Exercicio Exploratorio {sufixo}",
            categoria="Forca",
            rotulo="Agachamento",
            grupo_muscular="Pernas",
            equipamento="Barra",
            instrucao="Executar com postura adequada.",
            gif_url="https://example.com/exercicio-exp.gif",
        )
    )


def _criar_treino_exercicio(db_session, treino_id: str, exercicio_id: str):
    return TreinoExercicioService(db_session).criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino_id,
            exercicio_id=exercicio_id,
            series=4,
            repeticoes=10,
            descanso=90,
        )
    )


def _payload_execucao(usuario_id: str, treino_exercicio_id: str) -> ExecucaoCreate:
    return ExecucaoCreate(
        usuario_id=usuario_id,
        treino_exercicio_id=treino_exercicio_id,
        data_execucao=datetime.now(timezone.utc) - timedelta(minutes=5),
        carga=80.0,
        series=4,
        repeticoes=10,
        tempo_descanso_real=60,
        duracao_execucao=1800,
        calorias_queimadas=200,
        frequencia_cardiaca_media=130,
        observacoes="Exploratory test",
    )


# ---------------------------------------------------------------------------
# B1 — MemorySaver volátil
# ---------------------------------------------------------------------------

def test_b1_get_agente_usa_memory_saver():
    """
    FALHA ESPERADA: _get_agente() deve usar SqliteSaver como checkpointer
    para persistir estado entre restarts.

    No código atual (bugado), usa MemorySaver — estado é perdido em restarts.
    Este teste FALHA no código bugado porque assertamos que NÃO usa MemorySaver,
    mas ele usa. Após o fix (SqliteSaver), o teste passará.
    """
    from langgraph.checkpoint.memory import MemorySaver

    # Reseta o singleton para forçar recriação do agente
    agente_module._agente = None

    # Para evitar chamada real ao Gemini, mockamos a criação do LLM
    with patch("app.service.agente_service.ChatGoogleGenerativeAI") as mock_llm, \
         patch("app.service.agente_service.GEMINI_API_KEY", "fake-key"):
        mock_llm.return_value = MagicMock()
        agente = agente_module._get_agente()

    checkpointer = agente.checkpointer

    # FALHA ESPERADA no código bugado: checkpointer é MemorySaver.
    # Após o fix, assertamos que NÃO é MemorySaver (será SqliteSaver).
    assert not isinstance(checkpointer, MemorySaver), (
        "BUG 1 CONFIRMADO: checkpointer é MemorySaver — "
        "estado de conversa será perdido em restarts do processo. "
        "Fix necessário: substituir por SqliteSaver."
    )


# ---------------------------------------------------------------------------
# B2 — Dedup em RAM não sobrevive a reset do dict
# ---------------------------------------------------------------------------

def test_b2_dedup_nao_sobrevive_reset_do_dict():
    """
    FALHA ESPERADA: Após zerar _mensagens_processadas, o mesmo message_id
    é processado novamente (agente chamado 2x).

    Isso confirma o Bug 2 — a deduplicação está apenas em RAM e não
    persiste após restart do processo.
    """
    import app.api.whatsapp as whatsapp_module
    from app.api.whatsapp import _mensagem_duplicada

    message_id = "test-b2-unique-msg-id-12345"

    # Limpa o dict para garantir estado inicial limpo
    whatsapp_module._mensagens_processadas.clear()

    agente_chamado = []

    def fake_conversar(mensagem: str, thread_id: str):
        agente_chamado.append(thread_id)
        return {"resposta": "ok", "thread_id": thread_id, "model": "fake"}

    with patch.object(whatsapp_module._agente_service, "conversar", side_effect=fake_conversar):
        # Primeira chamada: registra o message_id no dict em memória
        primeiro = _mensagem_duplicada(message_id)
        assert not primeiro, "Primeira chamada não deve ser duplicata"

        # Simula restart: zera o dict em memória (como acontece em restart real)
        whatsapp_module._mensagens_processadas.clear()

        # Segunda chamada após "restart": sem persistência, trata como novo
        segundo = _mensagem_duplicada(message_id)

        # FALHA ESPERADA: no código bugado, após limpar o dict, a mensagem
        # não é detectada como duplicata. Após o fix (persistência em banco),
        # isso deve retornar True.
        assert segundo is True, (
            "BUG 2 CONFIRMADO: após zerar o dict em memória, o message_id "
            f"'{message_id}' não foi detectado como duplicata. "
            "Sem persistência em banco, restarts permitem reprocessamento."
        )


# ---------------------------------------------------------------------------
# B3 — registrar_execucao sem idempotência
# ---------------------------------------------------------------------------

def test_b3_registrar_execucao_duplicada_insere_dois_registros(db_session):
    """
    FALHA ESPERADA: Chamar registrar_execucao 2x com payload idêntico
    deve inserir APENAS 1 registro (idempotência). No código atual (bugado),
    insere 2 registros.

    Isso confirma o Bug 3 — ausência de verificação de duplicata em
    registrar_execucao.
    """
    usuario = _criar_usuario(db_session, "Usuario B3", "11920000001")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "b3")
    treino_exercicio = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    service = ExecucaoService(db_session)
    payload = _payload_execucao(usuario.id, treino_exercicio.id)

    # Primeira chamada — deve registrar
    resp1 = service.registrar_execucao(payload)

    # Segunda chamada com payload IDÊNTICO — deve retornar o mesmo registro
    resp2 = service.registrar_execucao(payload)

    # Lista execuções do usuário
    execucoes = service.listar_execucoes_por_usuario(usuario.id)

    # FALHA ESPERADA: no código bugado, o banco conterá 2 registros.
    # Após o fix (idempotência), deve conter apenas 1.
    assert len(execucoes) == 1, (
        f"BUG 3 CONFIRMADO: encontrados {len(execucoes)} registros para o mesmo payload. "
        "registrar_execucao não tem idempotência — insere duplicatas."
    )

    # Após o fix: os dois retornos devem ter o mesmo id
    assert resp1.id == resp2.id, (
        "BUG 3 CONFIRMADO: os dois retornos têm IDs diferentes, "
        "confirmando que dois registros foram inseridos."
    )


# ---------------------------------------------------------------------------
# B4 — _post() sem retry em RequestError
# ---------------------------------------------------------------------------

def test_b4_post_sem_retry_chama_httpx_apenas_uma_vez():
    """
    FALHA ESPERADA: Quando httpx.post lança RequestError, _post() deve
    tentar 3 vezes (retry com tenacity). No código atual (bugado), tenta
    apenas 1 vez.

    Isso confirma o Bug 4 — ausência de retry em _post().
    """
    service = WhatsappService()
    call_count = 0

    def fake_httpx_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise httpx.RequestError("Simulated network failure", request=MagicMock())

    with patch("httpx.post", side_effect=fake_httpx_post):
        resultado = service._post("http://fake-evolution-api/test", {"number": "5511999999999"})

    # _post() deve retornar False (não propagar exceção)
    assert resultado is False, "_post() deve retornar False em caso de RequestError"

    # FALHA ESPERADA: no código atual (bugado), httpx.post é chamado apenas 1x.
    # Após o fix (retry com tenacity), deve ser chamado 3x.
    assert call_count == 3, (
        f"BUG 4 CONFIRMADO: httpx.post foi chamado {call_count}x, esperado 3x. "
        "Sem retry, falhas transitórias de rede resultam em mensagens perdidas."
    )
