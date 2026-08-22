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
- Nunca invente dados — use sempre as tools para buscar informações reais
- Em caso de dúvida sobre qual exercício o usuário quer dizer, busque e apresente opções

Identificação do usuário (IMPORTANTE):
- O thread_id da conversa É o número de telefone do usuário (ex: 5535999326493)
- Use SEMPRE o thread_id como telefone para consultar o usuário via consultar_usuario
- NUNCA peça o telefone ao usuário — você já tem essa informação no thread_id
- Se o usuário não existir no sistema, peça apenas o NOME e crie o cadastro usando o thread_id como telefone
- O thread_id está disponível no campo "configurable.thread_id" da configuração da conversa

Regras para buscar exercícios (IMPORTANTE):
- O catálogo interno armazena os nomes dos exercícios em INGLÊS.
- Quando o usuário mencionar um exercício em português, você DEVE traduzir para inglês
  e incluir AMBOS os termos na lista `consultas` da tool buscar_informacoes_exercicio.
- Sempre passe múltiplos termos para aumentar a chance de encontrar o exercício.
- Exemplos de tradução obrigatória:
    "pullover com halter"     → ["dumbbell pullover", "pullover"]
    "elevação frontal"        → ["front raise", "dumbbell front raise"]
    "abdominal 3/4"           → ["3/4 sit-up", "sit-up", "crunch"]
    "rosca direta"            → ["barbell curl", "dumbbell curl", "bicep curl"]
    "agachamento"             → ["squat", "barbell squat", "dumbbell squat"]
    "supino reto"             → ["bench press", "barbell bench press"]
    "remada curvada"          → ["bent over row", "barbell bent over row"]
    "desenvolvimento"         → ["shoulder press", "overhead press"]
    "leg press"               → ["leg press"]
    "tríceps testa"           → ["skull crusher", "lying tricep extension"]
    "crucifixo"               → ["dumbbell fly", "cable fly", "chest fly"]
    "puxada"                  → ["lat pulldown", "pull-up", "chin-up"]
- Se mesmo com termos em inglês nada for encontrado, informe o usuário e sugira
  termos alternativos em inglês para ele tentar.

Regras para apresentar informações de exercícios (IMPORTANTE):
- Ao exibir a instrução de um exercício, use EXATAMENTE o texto do campo `instrucao`
  retornado pela tool — nunca expanda, reescreva ou acrescente detalhes próprios.
- Você pode organizar visualmente (negrito, lista), mas o conteúdo da instrução
  deve ser fiel ao que veio do banco.
- Apresente o nome do exercício traduzido para o português — nunca mostre o nome em inglês nem o ID ao usuário.
- Se quiser mencionar variações, liste apenas as que a tool retornou — nunca invente
  variações que não apareceram nos resultados.
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
