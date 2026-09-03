"""
Webhook da Evolution API.

Recebe eventos do WhatsApp, extrai a mensagem de texto e repassa
ao agente, devolvendo a resposta ao remetente.
"""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Body, Header, HTTPException, status

from app.core.config import (
    ENVIRONMENT,
    EVOLUTION_DEDUP_TTL_SECONDS,
    EVOLUTION_WEBHOOK_TOKEN,
)
from app.schemas.whatsapp import WhatsappWebhookPayload
from app.service.agente_service import AgenteService
from app.service.transcricao_service import TranscricaoService
from app.service.whatsapp_service import WhatsappService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

_agente_service = AgenteService()
_whatsapp_service = WhatsappService()

# Cache de deduplicação: message_id → timestamp
_mensagens_processadas: dict[str, float] = {}


def _ambiente_producao() -> bool:
    return ENVIRONMENT in {"prod", "production"}


def _mensagem_duplicada(message_id: str) -> bool:
    agora = time.monotonic()
    ttl = max(EVOLUTION_DEDUP_TTL_SECONDS, 1)

    # Limpa entradas expiradas
    expiradas = [mid for mid, ts in _mensagens_processadas.items() if agora - ts > ttl]
    for mid in expiradas:
        _mensagens_processadas.pop(mid, None)

    if message_id in _mensagens_processadas:
        return True

    _mensagens_processadas[message_id] = agora
    return False


def _verificar_token(token: str | None) -> None:
    if _ambiente_producao() and not EVOLUTION_WEBHOOK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook token não configurado para ambiente de produção.",
        )
    if not EVOLUTION_WEBHOOK_TOKEN:
        return
    if token != EVOLUTION_WEBHOOK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de webhook inválido.",
        )


@router.post("/webhook")
async def receber_mensagem(
    payload: object = Body(default=None),
    x_webhook_token: str | None = Header(default=None, alias="x-webhook-token"),
) -> dict:
    """
    Recebe eventos messages.upsert da Evolution API.

    Fluxo:
    1. Valida token de segurança.
    2. Ignora mensagens que não sejam texto recebido.
    3. Usa o número normalizado (sem DDI) como thread_id — garante
       isolamento por usuário e consistência com o banco.
    4. Envia ao agente e devolve a resposta ao número original.
    """
    _verificar_token(x_webhook_token)

    if not isinstance(payload, dict):
        return {"status": "ignored", "reason": "invalid_payload"}

    try:
        payload_model = WhatsappWebhookPayload.model_validate(payload)
    except Exception:
        logger.warning("Payload de webhook inválido recebido")
        return {"status": "ignored", "reason": "invalid_payload"}

    # Log temporário para diagnóstico de áudio
    if payload.get("data", {}).get("messageType") in ("audioMessage", "pttMessage"):
        logger.info("AUDIO RAW — messageType=%s data_keys=%s",
                    payload.get("data", {}).get("messageType"),
                    list(payload.get("data", {}).get("message", {}).keys()) if payload.get("data", {}).get("message") else [])
    else:
        # Log de qualquer messageType que chegue para diagnóstico
        mt = payload.get("data", {}).get("messageType", "N/A")
        ev = payload.get("event", "N/A")
        msg_keys = list(payload.get("data", {}).get("message", {}).keys()) if payload.get("data", {}).get("message") else []
        logger.info("WEBHOOK RAW — event=%s messageType=%s message_keys=%s", ev, mt, msg_keys)
        print(f"WEBHOOK RAW — event={ev} messageType={mt} message_keys={msg_keys}", flush=True)

    if payload_model.event not in ("messages.upsert", "message.upsert"):
        return {"status": "ignored", "reason": "event_not_handled"}

    # Número para envio de resposta (formato original da Evolution)
    numero_destino = payload_model.get_numero()
    if not numero_destino:
        return {"status": "ignored", "reason": "no_valid_number"}

    # Número normalizado (DDD + número) para usar como thread_id e no banco
    thread_id = payload_model.get_numero_contexto() or numero_destino

    texto = payload_model.get_texto()

    # Se for áudio, tenta transcrever
    if not texto and payload_model.is_audio():
        audio_url = payload_model.get_audio_url()
        # Log de diagnóstico — remove após resolver
        msg_data = payload_model.data.message
        logger.info(
            "DEBUG audio — is_audio=%s url=%s messageType=%s audioMessage_keys=%s",
            payload_model.is_audio(),
            audio_url,
            payload_model.data.messageType,
            list(msg_data.audioMessage.keys()) if msg_data and msg_data.audioMessage else None,
        )
        if audio_url:
            try:
                transcricao_service = TranscricaoService()
                texto = transcricao_service.transcrever_url(audio_url)
                logger.info("Áudio transcrito de %s: %s", numero_destino, texto[:80])
            except Exception as exc:
                logger.warning("Falha ao transcrever áudio: %s", exc)
                _whatsapp_service.enviar_resposta(
                    numero_destino,
                    "Não consegui transcrever seu áudio. Pode escrever o que precisa?"
                )
                return {"status": "ignored", "reason": "audio_transcription_failed"}
        else:
            return {"status": "ignored", "reason": "audio_without_url"}

    if not texto:
        return {"status": "ignored", "reason": "no_text_content"}

    # Ignora mensagens muito curtas que provavelmente são notificações de status
    if len(texto.strip()) < 2:
        return {"status": "ignored", "reason": "message_too_short"}

    # Deduplicação por message_id
    message_id = payload_model.get_message_id()
    if message_id and _mensagem_duplicada(message_id):
        logger.info("Mensagem duplicada ignorada: %s", message_id)
        return {"status": "ignored", "reason": "duplicate_message"}

    logger.info("Mensagem recebida de %s (thread: %s): %s", numero_destino, thread_id, texto[:80])

    try:
        resultado = _agente_service.conversar(
            mensagem=texto,
            thread_id=thread_id,
        )
        resposta = resultado["resposta"]
    except Exception as exc:
        logger.exception("Erro ao processar mensagem do agente: %s", exc)
        resposta = "Desculpe, ocorreu um erro interno. Tente novamente em instantes."

    try:
        _whatsapp_service.enviar_resposta(numero_destino, resposta)
    except Exception as exc:
        logger.exception("Erro ao enviar resposta via WhatsApp: %s", exc)

    return {"status": "ok"}
