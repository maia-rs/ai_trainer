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

# Magic bytes para detecção de formato
_MAGIC_BYTES: list[tuple[bytes, str, str]] = [
    (b"OggS", "audio.ogg", "audio/ogg"),
    (b"ID3", "audio.mp3", "audio/mpeg"),
    (b"\xff\xfb", "audio.mp3", "audio/mpeg"),
    (b"\xff\xf3", "audio.mp3", "audio/mpeg"),
    (b"\xff\xf2", "audio.mp3", "audio/mpeg"),
    (b"RIFF", "audio.wav", "audio/wav"),
    (b"fLaC", "audio.flac", "audio/flac"),
    (b"\x1aE\xdf\xa3", "audio.webm", "audio/webm"),
]


def _detectar_mimetype(dados: bytes, nome_arquivo: str) -> str:
    """Detecta o mimetype pelo conteúdo binário (magic bytes)."""
    for magic, _, mime in _MAGIC_BYTES:
        if dados[:len(magic)] == magic:
            return mime

    # Fallback: usa a extensão do nome
    ext = Path(nome_arquivo).suffix.lower()
    mapa = {
        ".ogg": "audio/ogg", ".opus": "audio/ogg",
        ".mp3": "audio/mpeg", ".mpeg": "audio/mpeg", ".mpga": "audio/mpeg",
        ".mp4": "audio/mp4", ".m4a": "audio/mp4",
        ".wav": "audio/wav", ".webm": "audio/webm",
    }
    return mapa.get(ext, "audio/ogg")  # ogg como fallback padrão do WhatsApp


def _nome_com_extensao(nome: str, dados: bytes) -> str:
    """Garante que o nome tem extensão compatível com o Whisper."""
    if Path(nome).suffix.lower() in _EXTENSOES_SUPORTADAS:
        return nome
    # Detecta extensão pelos magic bytes
    for magic, nome_padrao, _ in _MAGIC_BYTES:
        if dados[:len(magic)] == magic:
            return nome_padrao
    return "audio.ogg"


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

        # Headers para download — inclui autenticação da Evolution API se a URL for do servidor
        from app.core.config import EVOLUTION_API_KEY
        headers = {}
        if EVOLUTION_API_KEY and ("evolution" in url or "wppapi" in url or "wpp" in url):
            headers["apikey"] = EVOLUTION_API_KEY

        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Erro ao baixar áudio: {e}") from e

        # Verifica se recebeu áudio de verdade (não HTML de erro)
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type or len(resp.content) < 100:
            raise RuntimeError(
                f"URL retornou conteúdo inválido (content-type: {content_type}, "
                f"tamanho: {len(resp.content)} bytes). Verifique as credenciais de acesso."
            )

        # Detecta extensão pela URL ou pelo content-type
        nome = url.split("/")[-1].split("?")[0] or "audio.ogg"
        if "." not in nome:
            if "ogg" in content_type or "opus" in content_type:
                nome = "audio.ogg"
            elif "mpeg" in content_type or "mp3" in content_type:
                nome = "audio.mp3"
            elif "mp4" in content_type or "m4a" in content_type:
                nome = "audio.m4a"
            else:
                nome = "audio.ogg"

        logger.info("Áudio baixado: %d bytes, content-type: %s", len(resp.content), content_type)
        return self._chamar_api(resp.content, nome, idioma)

    def _chamar_api(self, dados: bytes, nome_arquivo: str, idioma: str) -> str:
        """Chama a API de transcrição do Groq."""
        # Garante extensão válida e detecta mimetype real pelos bytes
        nome_final = _nome_com_extensao(nome_arquivo, dados)
        mimetype = _detectar_mimetype(dados, nome_final)

        try:
            resp = httpx.post(
                _GROQ_TRANSCRIPTION_URL,
                headers=self._headers,
                files={"file": (nome_final, dados, mimetype)},
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
