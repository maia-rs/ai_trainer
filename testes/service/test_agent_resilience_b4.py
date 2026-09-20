from unittest.mock import MagicMock, patch
import httpx
import pytest
from app.service.whatsapp_service import WhatsappService


def test_post_retry_em_request_error():
    """httpx.post lança RequestError 2x, sucesso na 3ª → _post retorna True, chamado 3x."""
    service = WhatsappService()
    call_count = 0
    fake_resp = MagicMock()
    fake_resp.status_code = 200

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.RequestError("network error", request=MagicMock())
        return fake_resp

    with patch("httpx.post", side_effect=side_effect), \
         patch("tenacity.nap.sleep"):
        result = service._post("http://fake/test", {"number": "5511999"})

    assert result is True
    assert call_count == 3


def test_post_esgota_retries_retorna_false():
    """httpx.post sempre lança RequestError → _post retorna False após 3 tentativas."""
    service = WhatsappService()
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise httpx.RequestError("network error", request=MagicMock())

    with patch("httpx.post", side_effect=side_effect), \
         patch("tenacity.nap.sleep"):
        result = service._post("http://fake/test", {"number": "5511999"})

    assert result is False
    assert call_count == 3


def test_post_sem_retry_em_4xx():
    """4xx não deve acionar retry — chamado 1x, retorna False."""
    service = WhatsappService()
    call_count = 0
    fake_resp = MagicMock()
    fake_resp.status_code = 404
    fake_resp.text = "Not Found"

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return fake_resp

    with patch("httpx.post", side_effect=side_effect):
        result = service._post("http://fake/test", {"number": "5511999"})

    assert result is False
    assert call_count == 1


def test_post_sem_retry_em_5xx():
    """5xx não deve acionar retry — chamado 1x, retorna False."""
    service = WhatsappService()
    call_count = 0
    fake_resp = MagicMock()
    fake_resp.status_code = 500
    fake_resp.text = "Internal Server Error"

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return fake_resp

    with patch("httpx.post", side_effect=side_effect):
        result = service._post("http://fake/test", {"number": "5511999"})

    assert result is False
    assert call_count == 1


def test_post_sucesso_sem_retry():
    """Sucesso na primeira tentativa — chamado 1x, retorna True."""
    service = WhatsappService()
    call_count = 0
    fake_resp = MagicMock()
    fake_resp.status_code = 200

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return fake_resp

    with patch("httpx.post", side_effect=side_effect):
        result = service._post("http://fake/test", {"number": "5511999"})

    assert result is True
    assert call_count == 1


def test_get_audio_esgota_retries_retorna_none():
    """get_audio_base64 com RequestError em todas tentativas → retorna None sem propagar."""
    service = WhatsappService()
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise httpx.RequestError("audio network error", request=MagicMock())

    with patch("httpx.post", side_effect=side_effect), \
         patch("tenacity.nap.sleep"):
        result = service.get_audio_base64("msg-id-123", "5511999@s.whatsapp.net")

    assert result is None
    assert call_count == 3
