import os

from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.core.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    LANGSMITH_API_KEY,
    LANGSMITH_ENDPOINT,
    LANGSMITH_PROJECT,
    LANGSMITH_TRACING,
)
from app.tools.registry import get_agent_tools

_SYSTEM_PROMPT = """Você é o AITrainer, um assistente pessoal de treino inteligente.

Seu papel é ajudar o usuário a:
- Consultar e registrar seus treinos do dia
- Registrar execuções de exercícios (carga, séries, repetições)
- Acompanhar seu progresso e evolução física
- Gerenciar avaliações físicas
- Buscar informações sobre exercícios

Diretrizes de comportamento:
- Sempre responda em português brasileiro
- Seja objetivo e prático — o usuário está no contexto de um treino
- Antes de registrar qualquer dado, confirme com o usuário
- Quando buscar exercícios, apresente as opções e peça confirmação antes de adicionar a um treino
- Se o usuário não informar o usuario_id, consulte pelo telefone usando consultar_usuario
- Nunca invente dados — use sempre as tools para buscar informações reais
- Em caso de dúvida sobre qual exercício o usuário quer dizer, busque e apresente opções
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

    llm = ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0,
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

    def conversar(
        self,
        mensagem: str,
        thread_id: str,
    ) -> dict:
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY nao configurada. Verifique o arquivo .env."
            )

        agente = _get_agente()

        resultado = agente.invoke(
            {"messages": [("human", mensagem)]},
            config={"configurable": {"thread_id": thread_id}},
        )

        resposta = _extrair_texto_da_resposta(resultado)

        return {
            "thread_id": thread_id,
            "model": GROQ_MODEL,
            "resposta": resposta,
        }

    @staticmethod
    def verificar_health() -> tuple[dict, int]:
        groq_api_key_ok = bool(GROQ_API_KEY)
        groq_model_ok = bool(GROQ_MODEL)

        langsmith_enabled = bool(LANGSMITH_API_KEY)
        langsmith_api_key_ok = bool(LANGSMITH_API_KEY)

        faltantes = []
        if not groq_api_key_ok:
            faltantes.append("GROQ_API_KEY")
        if not groq_model_ok:
            faltantes.append("GROQ_MODEL")

        status = "ok" if not faltantes else "error"
        status_code = 200 if status == "ok" else 503

        payload = {
            "status": status,
            "provider": "groq",
            "checks": {
                "groq_api_key": groq_api_key_ok,
                "groq_model": GROQ_MODEL if groq_model_ok else None,
                "langsmith_enabled": langsmith_enabled,
                "langsmith_api_key": langsmith_api_key_ok,
            },
        }

        if faltantes:
            payload["missing"] = faltantes

        return payload, status_code
