"""
Script para testar o webhook do WhatsApp localmente.
Simula o payload que a Evolution API enviaria.

Uso:
    python scripts/testar_webhook.py
    python scripts/testar_webhook.py "como faço agachamento?"
    python scripts/testar_webhook.py "gera meu dashboard" --numero 5535999326493
"""
from __future__ import annotations

import sys
import httpx

# ── Configuração ──────────────────────────────────────────────────────────────
WEBHOOK_URL = "http://localhost:8000/whatsapp/webhook"
NUMERO      = "5535999326493"
MENSAGEM    = sys.argv[1] if len(sys.argv) > 1 else "oi, o que você pode fazer?"

# Permite passar --numero via args
for i, arg in enumerate(sys.argv):
    if arg == "--numero" and i + 1 < len(sys.argv):
        NUMERO = sys.argv[i + 1]

# ── Payload ───────────────────────────────────────────────────────────────────
payload = {
    "event": "messages.upsert",
    "instance": "AI_Trainer",
    "data": {
        "key": {
            "remoteJid": f"{NUMERO}@s.whatsapp.net",
            "fromMe": False,
            "id": "test-local-001",
        },
        "message": {"conversation": MENSAGEM},
        "messageType": "conversation",
        "pushName": "Rodrigo",
    },
}

print(f"Enviando para:  {WEBHOOK_URL}")
print(f"Número:         {NUMERO}")
print(f"Mensagem:       {MENSAGEM}")
print("-" * 60)

try:
    resp = httpx.post(WEBHOOK_URL, json=payload, timeout=60)
    print(f"Status:  {resp.status_code}")
    print(f"Resposta: {resp.json()}")
except httpx.ConnectError:
    print("ERRO: servidor não está rodando em localhost:8000")
except httpx.TimeoutException:
    print("TIMEOUT: o agente demorou mais de 60s para responder")
