"""
Testes para o webhook WhatsApp e o WhatsappService.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.whatsapp import WhatsappWebhookPayload
from app.service.whatsapp_service import WhatsappService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _payload(
    jid: str = "5535999326493@s.whatsapp.net",
    from_me: bool = False,
    texto: str = "olá",
    event: str = "messages.upsert",
    message_id: str = "abc123",
) -> dict:
    return {
        "event": event,
        "instance": "aitrainer",
        "data": {
            "key": {"remoteJid": jid, "fromMe": from_me, "id": message_id},
            "message": {"conversation": texto},
            "messageType": "conversation",
            "pushName": "Rodrigo",
        },
    }


# ---------------------------------------------------------------------------
# Testes do schema WhatsappWebhookPayload
# ---------------------------------------------------------------------------

class TestWhatsappWebhookPayload:

    def test_get_numero_retorna_digitos(self):
        p = WhatsappWebhookPayload(**_payload())
        # get_numero remove o DDI 55, retorna DDD + número
        assert p.get_numero() == "35999326493"

    def test_get_numero_ignora_from_me(self):
        p = WhatsappWebhookPayload(**_payload(from_me=True))
        assert p.get_numero() is None

    def test_get_numero_ignora_grupos(self):
        p = WhatsappWebhookPayload(**_payload(jid="1234567890-9876543210@g.us"))
        assert p.get_numero() is None

    def test_get_numero_contexto_remove_55(self):
        p = WhatsappWebhookPayload(**_payload(jid="5535999326493@s.whatsapp.net"))
        assert p.get_numero_contexto() == "35999326493"

    def test_get_numero_contexto_remove_zero_e_55(self):
        p = WhatsappWebhookPayload(**_payload(jid="05535999326493@s.whatsapp.net"))
        assert p.get_numero_contexto() == "35999326493"

    def test_get_texto_conversation(self):
        p = WhatsappWebhookPayload(**_payload(texto="agachamento"))
        assert p.get_texto() == "agachamento"

    def test_get_texto_extended(self):
        raw = _payload()
        raw["data"]["message"] = {
            "extendedTextMessage": {"text": "pullover com halter"}
        }
        p = WhatsappWebhookPayload(**raw)
        assert p.get_texto() == "pullover com halter"

    def test_get_texto_sem_mensagem(self):
        raw = _payload()
        raw["data"]["message"] = None
        p = WhatsappWebhookPayload(**raw)
        assert p.get_texto() is None

    def test_get_texto_vazio_retorna_none(self):
        raw = _payload(texto="   ")
        p = WhatsappWebhookPayload(**raw)
        assert p.get_texto() is None


# ---------------------------------------------------------------------------
# Testes do WhatsappService
# ---------------------------------------------------------------------------

class TestWhatsappService:

    def _service(self):
        svc = WhatsappService()
        svc._post = MagicMock()
        return svc

    def test_envia_texto_simples(self):
        svc = self._service()
        svc.enviar_resposta("5535999326493", "Olá, tudo bem?")
        svc._post.assert_called_once()
        args = svc._post.call_args[0]
        assert "sendText" in args[0]
        assert args[1]["text"] == "Olá, tudo bem?"

    def test_extrai_gif_e_envia_como_midia(self):
        svc = self._service()
        texto = (
            "Veja como executar:\n"
            "http://localhost:8000/exercises/videos/0375-AbCdEfG.gif\n"
            "Mantenha a postura correta."
        )
        svc.enviar_resposta("5535999326493", texto)

        assert svc._post.call_count == 2
        chamadas = [c[0] for c in svc._post.call_args_list]
        # primeira chamada: texto sem a URL do GIF
        assert "sendText" in chamadas[0][0]
        assert ".gif" not in chamadas[0][1]["text"]
        # segunda chamada: mídia
        assert "sendMedia" in chamadas[1][0]
        assert chamadas[1][1]["media"].endswith(".gif")

    def test_multiplos_gifs(self):
        svc = self._service()
        texto = (
            "Exercício 1: http://localhost:8000/exercises/videos/0001.gif\n"
            "Exercício 2: http://localhost:8000/exercises/videos/0002.gif"
        )
        svc.enviar_resposta("5535999326493", texto)
        # 1 texto + 2 mídias
        assert svc._post.call_count == 3

    def test_sem_gif_envia_apenas_texto(self):
        svc = self._service()
        svc.enviar_resposta("5535999326493", "Sem gif aqui.")
        assert svc._post.call_count == 1
        assert "sendText" in svc._post.call_args[0][0]

    def test_fallback_link_quando_envio_de_midia_falha(self):
        svc = WhatsappService()
        svc._post = MagicMock(side_effect=[True, False, True])

        texto = "Aqui está: http://localhost:8000/exercises/videos/0001.gif"
        svc.enviar_resposta("5535999326493", texto)

        assert svc._post.call_count == 3
        chamadas = [c[0] for c in svc._post.call_args_list]
        assert "sendText" in chamadas[0][0]
        assert "sendMedia" in chamadas[1][0]
        assert "sendText" in chamadas[2][0]
        assert "Link:" in chamadas[2][1]["text"]

    def test_remove_links_vazios_de_gif_do_texto(self):
        svc = self._service()
        texto = (
            "Supino com halteres\n"
            "[Ver animação do Supino com Halteres]()\n"
            "Mantenha a postura correta."
        )

        svc.enviar_resposta("5535999326493", texto)

        payload_texto = svc._post.call_args_list[0][0][1]
        assert "Ver animação do Supino com Halteres" not in payload_texto["text"]
        assert "[]" not in payload_texto["text"]
        assert "Mantenha a postura correta." in payload_texto["text"]

    def test_texto_vazio_nao_envia(self):
        """Se resposta for só GIF, envia mídia e também link clicável."""
        svc = self._service()
        svc.enviar_resposta(
            "5535999326493",
            "http://localhost:8000/exercises/videos/0001.gif"
        )
        chamadas_texto = [
            c for c in svc._post.call_args_list if "sendText" in c[0][0]
        ]
        chamadas_midia = [
            c for c in svc._post.call_args_list if "sendMedia" in c[0][0]
        ]
        assert len(chamadas_midia) == 1
        assert len(chamadas_texto) == 1
        assert "Link do GIF:" in chamadas_texto[0][0][1]["text"]

    def test_texto_longo_e_dividido_em_partes(self):
        svc = self._service()
        texto_longo = "\n".join([f"Linha {i} com instruções importantes" for i in range(1, 80)])

        svc.enviar_resposta("5535999326493", texto_longo)

        chamadas_texto = [
            c for c in svc._post.call_args_list if "sendText" in c[0][0]
        ]
        assert len(chamadas_texto) > 1
        for chamada in chamadas_texto:
            assert len(chamada[0][1]["text"]) <= 850


# ---------------------------------------------------------------------------
# Testes do endpoint webhook
# ---------------------------------------------------------------------------

class TestWebhookEndpoint:

    @pytest.fixture(autouse=True)
    def _patches(self):
        with (
            patch("app.api.whatsapp._agente_service") as mock_agente,
            patch("app.api.whatsapp._whatsapp_service") as mock_wpp,
            patch("app.api.whatsapp.ENVIRONMENT", "development"),
            patch("app.api.whatsapp._mensagens_processadas", {}),
        ):
            mock_agente.conversar.return_value = {"resposta": "Resposta do agente"}
            self.mock_agente = mock_agente
            self.mock_wpp = mock_wpp
            yield

    @property
    def client(self):
        return TestClient(app)

    def test_mensagem_valida_retorna_ok(self):
        resp = self.client.post("/whatsapp/webhook", json=_payload())
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_agente_chamado_com_thread_id_correto(self):
        self.client.post("/whatsapp/webhook", json=_payload())
        self.mock_agente.conversar.assert_called_once_with(
            mensagem="olá",
            thread_id="35999326493",
        )

    def test_resposta_enviada_ao_whatsapp(self):
        self.client.post("/whatsapp/webhook", json=_payload())
        self.mock_wpp.enviar_resposta.assert_called_once_with(
            "35999326493", "Resposta do agente"
        )

    def test_evento_ignorado_retorna_ignored(self):
        resp = self.client.post(
            "/whatsapp/webhook",
            json=_payload(event="messages.update"),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    def test_mensagem_propria_ignorada(self):
        resp = self.client.post(
            "/whatsapp/webhook",
            json=_payload(from_me=True),
        )
        assert resp.json()["status"] == "ignored"
        self.mock_agente.conversar.assert_not_called()

    def test_grupo_ignorado(self):
        resp = self.client.post(
            "/whatsapp/webhook",
            json=_payload(jid="1234567890-9876543210@g.us"),
        )
        assert resp.json()["status"] == "ignored"
        self.mock_agente.conversar.assert_not_called()

    def test_sem_texto_ignorado(self):
        raw = _payload()
        raw["data"]["message"] = None
        resp = self.client.post("/whatsapp/webhook", json=raw)
        assert resp.json()["status"] == "ignored"
        self.mock_agente.conversar.assert_not_called()

    def test_mensagem_duplicada_ignorada(self):
        payload = _payload(message_id="dup-001")

        primeira = self.client.post("/whatsapp/webhook", json=payload)
        segunda = self.client.post("/whatsapp/webhook", json=payload)

        assert primeira.status_code == 200
        assert primeira.json()["status"] == "ok"
        assert segunda.status_code == 200
        assert segunda.json() == {"status": "ignored", "reason": "duplicate_message"}
        self.mock_agente.conversar.assert_called_once()

    def test_token_invalido_retorna_401(self):
        with patch("app.api.whatsapp.EVOLUTION_WEBHOOK_TOKEN", "segredo123"):
            resp = self.client.post(
                "/whatsapp/webhook",
                json=_payload(),
                headers={"x-webhook-token": "errado"},
            )
        assert resp.status_code == 401

    def test_token_valido_aceito(self):
        with patch("app.api.whatsapp.EVOLUTION_WEBHOOK_TOKEN", "segredo123"):
            resp = self.client.post(
                "/whatsapp/webhook",
                json=_payload(),
                headers={"x-webhook-token": "segredo123"},
            )
        assert resp.status_code == 200

    def test_producao_sem_token_configurado_retorna_503(self):
        with (
            patch("app.api.whatsapp.ENVIRONMENT", "production"),
            patch("app.api.whatsapp.EVOLUTION_WEBHOOK_TOKEN", ""),
        ):
            resp = self.client.post("/whatsapp/webhook", json=_payload())
        assert resp.status_code == 503

    def test_erro_no_agente_responde_mensagem_de_fallback(self):
        self.mock_agente.conversar.side_effect = Exception("falha")
        resp = self.client.post("/whatsapp/webhook", json=_payload())
        assert resp.status_code == 200
        self.mock_wpp.enviar_resposta.assert_called_once()
        _, resposta = self.mock_wpp.enviar_resposta.call_args[0]
        assert "erro" in resposta.lower()

    def test_payload_invalido_retorna_ignored_sem_422(self):
        resp = self.client.post("/whatsapp/webhook", json={"foo": "bar"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"
        assert resp.json()["reason"] in {"invalid_payload", "event_not_handled"}
