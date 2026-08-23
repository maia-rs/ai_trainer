"""
Webhook da Evolution API.

Recebe eventos do WhatsApp, extrai a mensagem de texto e repassa
ao agente, devolvendo a resposta ao remetente.
"""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import (
    ENVIRONMENT,
    EVOLUTION_DEDUP_TTL_SECONDS,
    EVOLUTION_WEBHOOK_TOKEN,
)
from app.schemas.whatsapp import WhatsappWebhookPayload
from app.service.agente_service import AgenteService
from app.service.whatsapp_service import WhatsappService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

_agente_service = AgenteService()
_whatsapp_service = WhatsappService()
_mensagens_processadas: dict[str, float] = {}


def _ambiente_producao() -> bool:
    return ENVIRONMENT in {"prod", "production"}


def _mensagem_duplicada(message_id: str) -> bool:
    agora = time.monotonic()
    ttl = max(EVOLUTION_DEDUP_TTL_SECONDS, 1)

    # Limpa entradas expiradas para evitar crescimento indefinido.
    expiradas = [mid for mid, ts in _mensagens_processadas.items() if agora - ts > ttl]
    for mid in expiradas:
        _mensagens_processadas.pop(mid, None)

    if message_id in _mensagens_processadas:
        return True

    _mensagens_processadas[message_id] = agora
    return False


# ---------------------------------------------------------------------------
# Verificação de token (opcional mas recomendado)
# ---------------------------------------------------------------------------

def _verificar_token(token: str | None) -> None:
    """Rejeita requisições sem o token correto quando ele está configurado."""
    if _ambiente_producao() and not EVOLUTION_WEBHOOK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook token não configurado para ambiente de produção.",
        )

    if not EVOLUTION_WEBHOOK_TOKEN:
        return  # token não configurado → aceita tudo (dev local)

    if token != EVOLUTION_WEBHOOK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de webhook inválido.",
        )


# ---------------------------------------------------------------------------
# Endpoint principal
# ---------------------------------------------------------------------------

@router.post("/webhook")
async def receber_mensagem(
    payload: WhatsappWebhookPayload,
    x_webhook_token: str | None = Header(default=None, alias="x-webhook-token"),
) -> dict:
    """
    Recebe eventos messages.upsert da Evolution API.

    Fluxo:
    1. Valida o token de segurança (se configurado).
    2. Ignora eventos que não sejam mensagens de texto recebidas.
    3. Usa o número do remetente como thread_id (isolamento por usuário).
    4. Envia a mensagem ao agente e devolve a resposta ao WhatsApp.
    """
    _verificar_token(x_webhook_token)

    # Aceita apenas o evento de nova mensagem
    if payload.event not in ("messages.upsert", "message.upsert"):
        return {"status": "ignored", "reason": "event_not_handled"}

    numero = payload.get_numero()
    if not numero:
        return {"status": "ignored", "reason": "no_valid_number"}

    texto = payload.get_texto()
    if not texto:
        return {"status": "ignored", "reason": "no_text_content"}

    message_id = payload.get_message_id()
    if message_id and _mensagem_duplicada(message_id):
        return {"status": "ignored", "reason": "duplicate_message"}

    logger.info("Mensagem recebida de %s: %s", numero, texto[:80])

    try:
        resultado = _agente_service.conversar(
            mensagem=texto,
            thread_id=numero,
        )
        resposta = resultado["resposta"]
    except Exception as exc:
        logger.exception("Erro ao processar mensagem do agente: %s", exc)
        resposta = "Desculpe, ocorreu um erro interno. Tente novamente em instantes."

    try:
        _whatsapp_service.enviar_resposta(numero, resposta)
    except Exception as exc:
        logger.exception("Erro ao enviar resposta via WhatsApp: %s", exc)

    return {"status": "ok"}
