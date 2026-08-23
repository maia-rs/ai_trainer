from app.service import agente_service as agente_module
from app.service.agente_service import AgenteService


class DummyMessage:
    def __init__(self, content):
        self.content = content


class FakeAgent:
    def __init__(self, outputs):
        self._outputs = outputs
        self._i = 0
        self.calls = []

    def invoke(self, *_args, **_kwargs):
        self.calls.append((_args, _kwargs))
        saida = self._outputs[self._i]
        self._i += 1
        return saida


def test_garante_link_gif_quando_modelo_omite(monkeypatch):
    fake = FakeAgent(
        [
            {
                "messages": [
                    DummyMessage(
                        '{"items":[{"nome":"Smith Sumo Squat","gif_url":"https://aitrainer.orie.ia.br/exercises/videos/3142-dzz6BiV.gif"}]}'
                    ),
                    DummyMessage("GIF:"),
                ]
            }
        ]
    )

    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "ok")
    monkeypatch.setattr(agente_module, "_get_agente", lambda: fake)

    service = AgenteService()
    resultado = service.conversar("me manda o gif", "35999999999")

    assert "Link do GIF:" in resultado["resposta"]
    assert "3142-dzz6BiV.gif" in resultado["resposta"]


def test_usa_ultimo_exercicio_no_fallback_de_gif(monkeypatch):
    fake = FakeAgent(
        [
            {"messages": [DummyMessage("*Agachamento Sumo*\n1. Passo")]} ,
            {"messages": [DummyMessage("GIF:")]},
        ]
    )

    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "ok")
    monkeypatch.setattr(agente_module, "_get_agente", lambda: fake)

    def _fake_busca(self, nome_exercicio: str):
        assert "Agachamento Sumo" in nome_exercicio
        return "https://aitrainer.orie.ia.br/exercises/videos/3142-dzz6BiV.gif"

    monkeypatch.setattr(AgenteService, "_buscar_gif_por_nome", _fake_busca)

    service = AgenteService()
    service.conversar("como faço agachamento sumo?", "35999999999")
    resultado = service.conversar("me manda o gif", "35999999999")

    assert "Link do GIF:" in resultado["resposta"]
    assert "3142-dzz6BiV.gif" in resultado["resposta"]


def test_segura_contexto_geral_com_resumo_automatico(monkeypatch):
    outputs = [{"messages": [DummyMessage("ok")]} for _ in range(20)]
    fake = FakeAgent(outputs)

    monkeypatch.setattr(agente_module, "GEMINI_API_KEY", "ok")
    monkeypatch.setattr(agente_module, "_get_agente", lambda: fake)

    service = AgenteService()
    thread_id = "35999999999"

    for i in range(20):
        service.conversar(f"pedido geral {i}", thread_id)

    assert service._resumo_contexto.get(thread_id)

    ultimo_payload = fake.calls[-1][0][0]
    mensagem_enviada = ultimo_payload["messages"][0][1]
    assert "Resumo acumulado da conversa:" in mensagem_enviada
