"""
Testes do AgenteService — validam o comportamento de conversar()
sem depender da implementação interna do LangGraph ou Gemini.
"""
from unittest.mock import MagicMock, patch

from app.service import agente_service as agente_module
from app.service.agente_service import AgenteService


class DummyMessage:
    def __init__(self, content):
        self.content = content


class FakeAgent:
    def __init__(self, outputs):
        self._outputs = list(outputs)
        self._i = 0
        self.calls = []

    def invoke(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        saida = self._outputs[self._i % len(self._outputs)]
        self._i += 1
        return saida


def test_conversar_retorna_resposta(monkeypatch):
    fake = FakeAgent([{"messages": [DummyMessage("Olá, Rodrigo!")]}])
    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "ok")
    monkeypatch.setattr(agente_module, "_get_agente", lambda: fake)

    service = AgenteService()
    resultado = service.conversar("oi", "35999999999")

    assert resultado["resposta"] == "Olá, Rodrigo!"
    assert resultado["thread_id"] == "35999999999"


def test_conversar_injeta_numero_na_mensagem(monkeypatch):
    """Garante que o número do usuário é injetado no início da mensagem."""
    fake = FakeAgent([{"messages": [DummyMessage("ok")]}])
    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "ok")
    monkeypatch.setattr(agente_module, "_get_agente", lambda: fake)

    service = AgenteService()
    service.conversar("oi", "35999326493")

    mensagem_enviada = fake.calls[0][0][0]["messages"][0][1]
    assert "35999326493" in mensagem_enviada


def test_conversar_sem_api_key_lanca_erro(monkeypatch):
    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "")

    service = AgenteService()
    try:
        service.conversar("oi", "35999999999")
        assert False, "Deveria ter lançado ValueError"
    except ValueError as e:
        assert "API_KEY_GEMINI" in str(e)


def test_conversar_usa_thread_id_como_chave(monkeypatch):
    """Verifica que thread_id é passado corretamente ao LangGraph."""
    fake = FakeAgent([{"messages": [DummyMessage("ok")]}])
    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "ok")
    monkeypatch.setattr(agente_module, "_get_agente", lambda: fake)

    service = AgenteService()
    service.conversar("oi", "55123456789")

    # config é passado como kwarg ao invoke
    _, kwargs = fake.calls[0]
    config = kwargs.get("config", {})
    assert config.get("configurable", {}).get("thread_id") == "55123456789"


def test_resposta_lista_de_dicts_extraida_corretamente(monkeypatch):
    """Testa extração de conteúdo quando a mensagem vem como lista de dicts."""
    conteudo = [{"type": "text", "text": "Resposta em lista"}]
    fake = FakeAgent([{"messages": [DummyMessage(conteudo)]}])
    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "ok")
    monkeypatch.setattr(agente_module, "_get_agente", lambda: fake)

    service = AgenteService()
    resultado = service.conversar("oi", "35999999999")

    assert resultado["resposta"] == "Resposta em lista"


def test_resposta_vazia_retorna_fallback(monkeypatch):
    fake = FakeAgent([{"messages": []}])
    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "ok")
    monkeypatch.setattr(agente_module, "_get_agente", lambda: fake)

    service = AgenteService()
    resultado = service.conversar("oi", "35999999999")

    assert resultado["resposta"]  # não vazio
