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

_MAX_TEXT_CHARS = 850

# Regex para detectar URLs de GIF na resposta do agente
# Captura URLs diretas e dentro de markdown [texto](url) ou entre parênteses
_GIF_PATTERN = re.compile(r'https?://[^\s\)\]]+\.gif', re.IGNORECASE)
_EMPTY_MARKDOWN_LINK_PATTERN = re.compile(r'(?<!\!)\[[^\]]*\]\(\s*\)', re.IGNORECASE)
_MARKDOWN_GIF_LINK_PATTERN = re.compile(
    r'(?<!\!)\[[^\]]*\]\((https?://[^\s)]+\.gif(?:\?[^\s)]*)?)\)',
    re.IGNORECASE,
)


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
        texto = _EMPTY_MARKDOWN_LINK_PATTERN.sub("", texto)
        texto = _MARKDOWN_GIF_LINK_PATTERN.sub(r"\1", texto)

        gifs = _GIF_PATTERN.findall(texto)
        texto_limpo = _GIF_PATTERN.sub("", texto).strip()

        # Remove linhas que ficaram vazias após remover os GIFs
        linhas = [l for l in texto_limpo.splitlines() if l.strip()]
        texto_limpo = "\n".join(linhas).strip()
        somente_gif = bool(gifs) and not texto_limpo

        # Envia o texto principal (em partes quando necessário)
        if texto_limpo:
            for parte in self._quebrar_texto(texto_limpo, max_chars=_MAX_TEXT_CHARS):
                self._enviar_texto(numero, parte)

        # Envia cada GIF como mídia
        for url in gifs:
            enviado = self._enviar_midia(numero, url, caption="")
            if not enviado:
                # Fallback: se a API de mídia falhar, envia o link como texto.
                self._enviar_texto(numero, f"Não consegui enviar o GIF como mídia. Link: {url}")
                continue

            # Alguns clientes não renderizam GIF mesmo com ACK da API.
            # Quando a resposta era só GIF, manda também o link clicável.
            if somente_gif:
                self._enviar_texto(numero, f"Link do GIF: {url}")

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _enviar_texto(self, numero: str, texto: str) -> bool:
        payload = {
            "number": numero,
            "text": texto,
        }
        return self._post(f"{self._base}/sendText/{EVOLUTION_INSTANCE}", payload)

    def _quebrar_texto(self, texto: str, max_chars: int = _MAX_TEXT_CHARS) -> list[str]:
        """Quebra texto longo em partes menores, preservando legibilidade."""
        texto = (texto or "").strip()
        if not texto:
            return []
        if len(texto) <= max_chars:
            return [texto]

        blocos: list[str] = []
        atual = ""

        for paragrafo in texto.split("\n"):
            paragrafo = paragrafo.strip()
            if not paragrafo:
                continue

            candidato = f"{atual}\n{paragrafo}".strip() if atual else paragrafo
            if len(candidato) <= max_chars:
                atual = candidato
                continue

            if atual:
                blocos.append(atual)
                atual = ""

            if len(paragrafo) <= max_chars:
                atual = paragrafo
                continue

            palavras = paragrafo.split()
            parcial = ""
            for palavra in palavras:
                candidato_palavra = f"{parcial} {palavra}".strip() if parcial else palavra
                if len(candidato_palavra) <= max_chars:
                    parcial = candidato_palavra
                else:
                    if parcial:
                        blocos.append(parcial)
                    parcial = palavra
            if parcial:
                atual = parcial

        if atual:
            blocos.append(atual)

        return blocos

    def _enviar_midia(self, numero: str, url: str, caption: str = "") -> bool:
        """Envia imagem/GIF via URL."""
        payload = {
            "number": numero,
            "mediatype": "image",
            "mimetype": "image/gif",
            "caption": caption,
            "media": url,
            "fileName": url.split("/")[-1],
        }
        resultado = self._post(f"{self._base}/sendMedia/{EVOLUTION_INSTANCE}", payload, timeout=45)
        logger.info("sendMedia para %s url=%s resultado=%s", numero, url, resultado)
        return resultado

    def _post(self, url: str, payload: dict, timeout: int = 15) -> bool:
        try:
            resp = httpx.post(url, json=payload, headers=self._headers, timeout=timeout)
            if resp.status_code not in (200, 201):
                logger.warning(
                    "Evolution API retornou %s para %s: %s",
                    resp.status_code, url, resp.text[:200],
                )
                return False
            return True
        except httpx.RequestError as exc:
            logger.error("Erro ao chamar Evolution API (%s): %s", url, exc)
            return False
