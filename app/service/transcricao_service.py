"""
Serviço de transcrição de áudio via Groq Whisper API.

Suporta:
- Arquivo local (path)
- Bytes em memória
- URL pública (baixa e transcreve)
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import httpx

from app.core.config import GROQ_API_KEY, GROQ_WHISPER_MODEL

logger = logging.getLogger(__name__)

_GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

# Formatos suportados pelo Whisper via Groq
_EXTENSOES_SUPORTADAS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".ogg", ".opus"}


class TranscricaoService:
    """Transcreve áudio usando Groq Whisper API."""

    def __init__(self) -> None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY não configurada.")
        self._headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    def transcrever_arquivo(self, caminho: str | Path, idioma: str = "pt") -> str:
        """Transcreve um arquivo de áudio local."""
        caminho = Path(caminho)
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        sufixo = caminho.suffix.lower()
        if sufixo not in _EXTENSOES_SUPORTADAS:
            raise ValueError(f"Formato não suportado: {sufixo}. Use: {_EXTENSOES_SUPORTADAS}")

        with open(caminho, "rb") as f:
            return self._chamar_api(f.read(), caminho.name, idioma)

    def transcrever_bytes(self, dados: bytes, nome_arquivo: str = "audio.ogg", idioma: str = "pt") -> str:
        """Transcreve áudio a partir de bytes em memória."""
        return self._chamar_api(dados, nome_arquivo, idioma)

    def transcrever_url(self, url: str, idioma: str = "pt") -> str:
        """Baixa o áudio de uma URL e transcreve."""
        logger.info("Baixando áudio de %s", url)
        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Erro ao baixar áudio: {e}") from e

        # Detecta extensão pela URL ou usa .ogg (padrão WhatsApp)
        nome = url.split("/")[-1].split("?")[0] or "audio.ogg"
        if "." not in nome:
            nome = "audio.ogg"

        return self._chamar_api(resp.content, nome, idioma)

    def _chamar_api(self, dados: bytes, nome_arquivo: str, idioma: str) -> str:
        """Chama a API de transcrição do Groq."""
        try:
            resp = httpx.post(
                _GROQ_TRANSCRIPTION_URL,
                headers=self._headers,
                files={"file": (nome_arquivo, dados, "audio/ogg")},
                data={
                    "model": GROQ_WHISPER_MODEL,
                    "language": idioma,
                    "response_format": "text",
                },
                timeout=60,
            )
            resp.raise_for_status()
            return resp.text.strip()
        except httpx.HTTPStatusError as e:
            logger.error("Groq Whisper erro %s: %s", e.response.status_code, e.response.text[:200])
            raise RuntimeError(f"Erro na API Whisper: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Erro de conexão com Groq: {e}") from e
