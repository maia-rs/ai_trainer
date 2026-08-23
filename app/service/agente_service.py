import os
import re
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LANGSMITH_API_KEY,
    LANGSMITH_ENDPOINT,
    LANGSMITH_PROJECT,
    LANGSMITH_TRACING,
)
from app.tools.registry import get_agent_tools

# Detecta URL de GIF — captura mesmo dentro de markdown [texto](url)
_GIF_URL_PATTERN = re.compile(r"https?://[^\s\)\]]+\.gif", re.IGNORECASE)

_SYSTEM_PROMPT = """Você é o AITrainer, assistente pessoal de treino no WhatsApp.

Responda sempre em português do Brasil. Seja objetivo e prático.

━━ IDENTIFICAÇÃO DO USUÁRIO ━━
- O número de telefone do usuário é o thread_id da conversa (ex: 35999326493).
- Na PRIMEIRA mensagem de cada conversa, chame consultar_usuario com esse número.
- Se o usuário não existir, peça apenas o NOME e chame criar_usuario.
- Após identificar o usuário, NÃO chame consultar_usuario novamente a menos que o
  usuário peça explicitamente trocar de conta.

━━ BUSCA DE EXERCÍCIOS ━━
- O catálogo usa nomes em INGLÊS. Sempre traduza e passe múltiplos termos:
    "supino reto"      → ["bench press", "barbell bench press"]
    "agachamento"      → ["squat", "barbell squat"]
    "rosca direta"     → ["barbell curl", "dumbbell curl"]
    "pullover"         → ["dumbbell pullover", "pullover"]
    "elevação frontal" → ["front raise", "dumbbell front raise"]
    "crucifixo"        → ["dumbbell fly", "cable fly"]
    "puxada"           → ["lat pulldown", "pull-up", "chin-up"]
    "desenvolvimento"  → ["shoulder press", "overhead press"]
    "abdominal 3/4"    → ["3/4 sit-up", "sit-up", "crunch"]

━━ APRESENTAÇÃO DE EXERCÍCIOS ━━
- Use o texto EXATO do campo `instrucao` retornado pela tool.
- Traduza o nome para português ao apresentar ao usuário.
- Inclua SEMPRE o campo `gif_url` na resposta quando disponível — coloque a URL
  completa terminando em .gif diretamente no texto (não use markdown de link).
- Se o usuário pedir "o gif" sem especificar exercício, use o gif_url do último
  exercício citado na conversa.

━━ AVALIAÇÃO FÍSICA ━━
- Se o usuário informar água corporal em litros, converta para %:
  formula: (litros / peso_kg) * 100. Ex: 39.1 L ÷ 90.2 kg = 43.3%
- Campos obrigatórios: peso, altura, percentual_gordura, massa_gorda,
  massa_muscular, imc, gordura_visceral, agua_corporal (%), taxa_metabolica_basal.

━━ REGRAS GERAIS ━━
- Confirme antes de registrar qualquer dado.
- Nunca invente dados — use sempre as tools.
- Respostas curtas e diretas — máximo 5 linhas por bloco.
- Não repita informações já ditas na mesma conversa.
"""


def _configurar_langsmith() -> None:
    if LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
        os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT
        os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
        os.environ["LANGSMITH_TRACING"] = LANGSMITH_TRACING
        os.environ["LANGCHAIN_TRACING_V2"] = LANGSMITH_TRACING


def _criar_agente():
    _configurar_langsmith()

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0,
    )

    return create_react_agent(
        model=llm,
        tools=get_agent_tools(),
        checkpointer=MemorySaver(),
        prompt=SystemMessage(content=_SYSTEM_PROMPT),
    )


_agente = None


def _get_agente():
    global _agente
    if _agente is None:
        _agente = _criar_agente()
    return _agente


def _extrair_texto_da_resposta(resultado: dict) -> str:
    mensagens = resultado.get("messages", [])
    if not mensagens:
        return "Não foi possível gerar uma resposta."

    ultima = mensagens[-1]
    conteudo = getattr(ultima, "content", "")

    if isinstance(conteudo, str):
        return conteudo

    if isinstance(conteudo, list):
        partes = []
        for item in conteudo:
            if isinstance(item, dict) and item.get("type") == "text":
                partes.append(item.get("text", ""))
            elif isinstance(item, str):
                partes.append(item)
        return "\n".join(p for p in partes if p).strip() or "Resposta vazia."

    return str(conteudo)


class AgenteService:
    """Serviço de orquestração do agente com Gemini e LangSmith."""

    def conversar(self, mensagem: str, thread_id: str) -> dict:
        if not GEMINI_API_KEY:
            raise ValueError("API_KEY_GEMINI não configurada. Verifique o arquivo .env.")

        agente = _get_agente()

        resultado = agente.invoke(
            {"messages": [("human", mensagem)]},
            config={"configurable": {"thread_id": thread_id}},
        )

        resposta = _extrair_texto_da_resposta(resultado)

        return {
            "thread_id": thread_id,
            "model": GEMINI_MODEL,
            "resposta": resposta,
        }

    @staticmethod
    def verificar_health() -> tuple[dict, int]:
        gemini_api_key_ok = bool(GEMINI_API_KEY)
        gemini_model_ok = bool(GEMINI_MODEL)
        langsmith_enabled = bool(LANGSMITH_API_KEY)

        faltantes = []
        if not gemini_api_key_ok:
            faltantes.append("API_KEY_GEMINI")
        if not gemini_model_ok:
            faltantes.append("GEMINI_MODEL")

        status = "ok" if not faltantes else "error"
        status_code = 200 if status == "ok" else 503

        payload = {
            "status": status,
            "provider": "google-gemini",
            "checks": {
                "gemini_api_key": gemini_api_key_ok,
                "gemini_model": GEMINI_MODEL if gemini_model_ok else None,
                "langsmith_enabled": langsmith_enabled,
            },
        }

        if faltantes:
            payload["missing"] = faltantes

        return payload, status_code
