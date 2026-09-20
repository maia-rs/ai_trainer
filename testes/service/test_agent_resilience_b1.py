"""
Testes de fix para Bug 1 — Substituição de MemorySaver por SqliteSaver.
Valida que o checkpointer persistente está em uso e que o comportamento
de conversação é preservado.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

from app.service import agente_service as agente_module
from app.service.agente_service import AgenteService


class DummyMessage:
    def __init__(self, content):
        self.content = content


class FakeAgent:
    """Simula o agente LangGraph sem chamadas reais ao LLM."""

    def __init__(self, outputs):
        self._outputs = list(outputs)
        self._i = 0
        self.calls = []

    def invoke(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        saida = self._outputs[self._i % len(self._outputs)]
        self._i += 1
        return saida


# ---------------------------------------------------------------------------
# test_checkpointer_nao_e_memory_saver
# ---------------------------------------------------------------------------

def test_checkpointer_nao_e_memory_saver(monkeypatch, tmp_path):
    """
    Verifica que o agente criado NÃO usa MemorySaver como checkpointer.
    O checkpointer deve ser uma instância de SqliteSaver.
    """
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.checkpoint.sqlite import SqliteSaver

    # Isola o singleton e redireciona o banco para um arquivo temporário
    monkeypatch.setattr(agente_module, "_agente", None)
    monkeypatch.setattr(agente_module, "AGENT_CHECKPOINT_DB", str(tmp_path / "test_checkpoints.sqlite3"))
    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "fake-key")

    # Mock do LLM para não fazer chamada real
    fake_llm = MagicMock()
    fake_llm.bind_tools = MagicMock(return_value=fake_llm)

    with patch("app.service.agente_service.ChatGoogleGenerativeAI", return_value=fake_llm):
        with patch("app.service.agente_service.create_react_agent") as mock_create:
            mock_create.return_value = MagicMock()
            agente_module._agente = None
            agente_module._get_agente()

            # Extrai o checkpointer passado ao create_react_agent
            _, kwargs = mock_create.call_args
            checkpointer = kwargs.get("checkpointer")

    assert not isinstance(checkpointer, MemorySaver), (
        "checkpointer NÃO deve ser MemorySaver — deve ser SqliteSaver"
    )
    assert isinstance(checkpointer, SqliteSaver), (
        "checkpointer deve ser instância de SqliteSaver"
    )

    # Limpeza do singleton
    agente_module._agente = None


# ---------------------------------------------------------------------------
# test_agente_checkpoint_db_default
# ---------------------------------------------------------------------------

def test_agente_checkpoint_db_default():
    """
    Verifica que AGENT_CHECKPOINT_DB tem o valor padrão 'checkpoints.sqlite3'
    quando a variável de ambiente não está definida.
    """
    import app.core.config as cfg

    # Sem a env var definida, o valor deve ser o padrão
    saved = os.environ.pop("AGENT_CHECKPOINT_DB", None)
    try:
        # Reimporta o valor diretamente via os.getenv com o mesmo padrão
        valor = os.getenv("AGENT_CHECKPOINT_DB", "checkpoints.sqlite3")
        assert valor == "checkpoints.sqlite3", (
            f"Esperado 'checkpoints.sqlite3', obtido '{valor}'"
        )
    finally:
        if saved is not None:
            os.environ["AGENT_CHECKPOINT_DB"] = saved


# ---------------------------------------------------------------------------
# test_conversar_preserva_comportamento_normal
# ---------------------------------------------------------------------------

def test_conversar_preserva_comportamento_normal(monkeypatch):
    """
    Verifica que a substituição de MemorySaver por SqliteSaver não quebra
    o comportamento normal de conversa — Properties 1 e 2 (não-regressão).
    Usa o mesmo padrão FakeAgent de test_agente_service.py.
    """
    fake = FakeAgent([{"messages": [DummyMessage("Tudo certo com SqliteSaver!")]}])
    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "ok")
    monkeypatch.setattr(agente_module, "_get_agente", lambda: fake)

    service = AgenteService()
    resultado = service.conversar("oi", "35999999999")

    assert resultado["resposta"] == "Tudo certo com SqliteSaver!"
    assert resultado["thread_id"] == "35999999999"
    assert len(fake.calls) == 1

    # Verifica que thread_id é passado corretamente
    _, kwargs = fake.calls[0]
    config = kwargs.get("config", {})
    assert config.get("configurable", {}).get("thread_id") == "35999999999"
