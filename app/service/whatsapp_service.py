"""
Cliente para a Evolution API.

Responsável por enviar mensagens de texto, links e mídias (GIFs)
de volta ao usuário no WhatsApp.
"""
from __future__ import annotations

import logging
import re

import httpx

from app.core.config import (
    EVOLUTION_API_KEY,
    EVOLUTION_API_URL,
    EVOLUTION_INSTANCE,
)

logger = logging.getLogger(__name__)

# Regex para detectar URLs de GIF na resposta do agente
_GIF_PATTERN = re.compile(r'https?://\S+\.gif\b', re.IGNORECASE)


class WhatsappService:
    """Serviço de envio de mensagens via Evolution API."""

    def __init__(self) -> None:
        self._base = f"{EVOLUTION_API_URL}/message"
        self._headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def enviar_resposta(self, numero: str, texto: str) -> None:
        """
        Envia a resposta do agente ao usuário.

        - Extrai URLs de GIF do texto e envia cada uma como mídia separada.
        - Envia o texto (sem as URLs de GIF) como mensagem de texto.
        - Se o texto contiver um link de dashboard, envia como link com preview.
        """
        gifs = _GIF_PATTERN.findall(texto)
        texto_limpo = _GIF_PATTERN.sub("", texto).strip()

        # Remove linhas que ficaram vazias após remover os GIFs
        linhas = [l for l in texto_limpo.splitlines() if l.strip()]
        texto_limpo = "\n".join(linhas).strip()

        # Envia o texto principal
        if texto_limpo:
            self._enviar_texto(numero, texto_limpo)

        # Envia cada GIF como mídia
        for url in gifs:
            self._enviar_midia(numero, url, caption="")

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _enviar_texto(self, numero: str, texto: str) -> None:
        payload = {
            "number": numero,
            "text": texto,
        }
        self._post(f"{self._base}/sendText/{EVOLUTION_INSTANCE}", payload)

    def _enviar_midia(self, numero: str, url: str, caption: str = "") -> None:
        """Envia imagem/GIF via URL."""
        payload = {
            "number": numero,
            "mediatype": "image",
            "mimetype": "image/gif",
            "caption": caption,
            "media": url,
            "fileName": url.split("/")[-1],
        }
        self._post(f"{self._base}/sendMedia/{EVOLUTION_INSTANCE}", payload)

    def _post(self, url: str, payload: dict) -> None:
        try:
            resp = httpx.post(url, json=payload, headers=self._headers, timeout=15)
            if resp.status_code not in (200, 201):
                logger.warning(
                    "Evolution API retornou %s para %s: %s",
                    resp.status_code, url, resp.text[:200],
                )
        except httpx.RequestError as exc:
            logger.error("Erro ao chamar Evolution API (%s): %s", url, exc)
