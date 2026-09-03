from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Payload recebido da Evolution API (webhook)
# ---------------------------------------------------------------------------

class WhatsappMessageKey(BaseModel):
    remoteJid: str = ""
    fromMe: bool = False
    id: str = ""


class WhatsappMessageContent(BaseModel):
    conversation: str | None = None
    extendedTextMessage: dict[str, Any] | None = None
    audioMessage: dict[str, Any] | None = None
    imageMessage: dict[str, Any] | None = None


class WhatsappMessageData(BaseModel):
    key: WhatsappMessageKey = Field(default_factory=WhatsappMessageKey)
    message: WhatsappMessageContent | None = None
    messageType: str = ""
    pushName: str | None = None


class WhatsappWebhookPayload(BaseModel):
    """Payload genérico enviado pela Evolution API no evento messages.upsert."""
    event: str = ""
    instance: str = ""
    data: WhatsappMessageData = Field(default_factory=WhatsappMessageData)

    def get_message_id(self) -> str | None:
        """Retorna o ID único da mensagem quando disponível."""
        message_id = self.data.key.id.strip()
        return message_id or None

    def get_numero(self) -> str | None:
        """Retorna o número do remetente no formato que a Evolution usa para envio (com DDI)."""
        jid = self.data.key.remoteJid
        if not jid or self.data.key.fromMe:
            return None
        numero = jid.split("@")[0]
        if "-" in numero:
            return None
        return numero

    def get_numero_contexto(self) -> str | None:
        """Normaliza o número para DDD+numero (10 ou 11 dígitos) no contexto do agente."""
        numero = self.get_numero()
        if not numero:
            return None

        digitos = "".join(ch for ch in numero if ch.isdigit())
        # Remove zeros à esquerda comuns em números de discagem
        while len(digitos) > 11 and digitos.startswith("0"):
            digitos = digitos[1:]

        # Remove DDI do Brasil quando presente (55)
        if len(digitos) in (12, 13) and digitos.startswith("55"):
            digitos = digitos[2:]

        if len(digitos) in (10, 11):
            return digitos

        # Fallback: usa o número original caso não seja possível normalizar.
        return numero

    def get_texto(self) -> str | None:
        """Extrai o texto da mensagem (conversation ou extended text)."""
        msg = self.data.message
        if not msg:
            return None
        if msg.conversation:
            return msg.conversation.strip() or None
        if msg.extendedTextMessage:
            return (msg.extendedTextMessage.get("text") or "").strip() or None
        return None

    def is_audio(self) -> bool:
        """Retorna True se a mensagem for um áudio."""
        msg = self.data.message
        if not msg:
            return False
        return msg.audioMessage is not None or self.data.messageType in ("audioMessage", "pttMessage")

    def get_audio_url(self) -> str | None:
        """Retorna a URL de download do áudio, se disponível."""
        msg = self.data.message
        if not msg or not msg.audioMessage:
            return None
        return msg.audioMessage.get("url") or msg.audioMessage.get("mediaUrl") or None

    def get_remote_jid(self) -> str | None:
        """Retorna o remoteJid bruto da mensagem (ex: 5511999998888@s.whatsapp.net)."""
        jid = self.data.key.remoteJid
        return jid if jid else None
