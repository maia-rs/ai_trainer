import os

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

_SYSTEM_PROMPT = """Você é o AITrainer, um assistente de treino em WhatsApp.

Objetivo:
- responder em português do Brasil
- ser prático e objetivo
- usar as tools para buscar informações reais
- confirmar antes de registrar qualquer dado

Regras principais:
- não invente dados
- use sempre o número do usuário como thread_id
- trate o número do thread_id como número já confirmado do usuário
- não peça telefone novamente se o número já estiver no contexto
- só peça telefone se o usuário quiser consultar outro número explicitamente
- para exercícios, traduza o nome para inglês e passe vários termos na tool
- se não encontrar, diga que não encontrou e sugira alternativas em inglês
- responda em poucas frases, sem repetir informações
- ao mostrar instrução de exercício, use o texto da tool exatamente, apenas organizando visualmente
- se o usuário pedir "o gif" sem repetir o nome, use o último exercício citado na conversa
- ao enviar GIF, inclua sempre a URL completa terminando em .gif (sem esconder o link)
- nunca responda "aqui está o gif" sem incluir o link .gif na mesma mensagem

Exemplos de busca obrigatórios:
- "supino reto" → ["bench press", "barbell bench press"]
- "agachamento" → ["squat", "barbell squat", "dumbbell squat"]
- "rosca direta" → ["barbell curl", "dumbbell curl", "bicep curl"]
- "crucifixo" → ["dumbbell fly", "cable fly", "chest fly"]

Formato de resposta:
- curta e direta
- nome do exercício em português
- instrução do banco, sem acrescentar detalhes
- se houver GIF, só mencione o link da animação quando for relevante
- quando o usuário pedir GIF, retorne explicitamente o campo gif_url vindo da tool
"""


def _configurar_langsmith() -> None:
    """Configura as variáveis de ambiente do LangSmith se a chave estiver disponível."""
    if LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
        os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT
        os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
        os.environ["LANGSMITH_TRACING"] = LANGSMITH_TRACING
        os.environ["LANGCHAIN_TRACING_V2"] = LANGSMITH_TRACING


def _criar_agente():
    """Cria e retorna a instância do agente com MemorySaver."""
    _configurar_langsmith()

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0,
        max_output_tokens=180,
    )

    return create_react_agent(
        model=llm,
        tools=get_agent_tools(),
        checkpointer=MemorySaver(),
        prompt=SystemMessage(content=_SYSTEM_PROMPT),
    )


# Instância única do agente — compartilha o MemorySaver entre requests
_agente = None


def _get_agente():
    global _agente
    if _agente is None:
        _agente = _criar_agente()
    return _agente


def _extrair_texto_da_resposta(resultado: dict) -> str:
    """Extrai o texto da última mensagem do resultado do agente."""
    mensagens = resultado.get("messages", [])
    if not mensagens:
        return "Nao foi possivel gerar uma resposta."

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
        return "\n".join(parte for parte in partes if parte).strip() or "Resposta vazia."

    return str(conteudo)


class AgenteService:
    """Servico de orquestracao do agente com Groq e LangSmith."""

    def __init__(self) -> None:
        self._historico: dict[str, list[str]] = {}

    @staticmethod
    def _contexto_telefone(thread_id: str) -> str:
        return (
            "Contexto fixo da conversa:\n"
            f"- numero_whatsapp_confirmado: {thread_id}\n"
            "- use esse número como padrão nas tools de usuário/treino/dashboard\n"
            "- não solicite telefone novamente sem pedido explícito de troca"
        )

    def _mensagem_com_contexto(self, thread_id: str, mensagem: str) -> str:
        """Monta contexto curto com telefone confirmado e histórico recente."""
        historico = self._historico.get(thread_id, [])
        recente = historico[-6:]
        contexto_fixo = self._contexto_telefone(thread_id)

        if not recente:
            return f"{contexto_fixo}\n\nUsuário: {mensagem}"

        return (
            f"{contexto_fixo}\n\n"
            "Histórico recente:\n"
            + "\n".join(recente)
            + "\n\nUsuário: "
            + mensagem
        )

    def conversar(
        self,
        mensagem: str,
        thread_id: str,
    ) -> dict:
        if not GEMINI_API_KEY:
            raise ValueError(
                "API_KEY_GEMINI nao configurada. Verifique o arquivo .env."
            )

        agente = _get_agente()
        mensagem_para_modelo = self._mensagem_com_contexto(thread_id, mensagem)

        resultado = agente.invoke(
            {"messages": [("human", mensagem_para_modelo)]},
            config={"configurable": {"thread_id": thread_id}},
        )

        resposta = _extrair_texto_da_resposta(resultado)

        historico = self._historico.setdefault(thread_id, [])
        historico.extend([f"Usuário: {mensagem}", f"Assistente: {resposta}"])
        if len(historico) > 12:
            historico[:] = historico[-12:]

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
