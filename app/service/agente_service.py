import os
import re
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
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
from app.core.database import SessionLocal
from app.service.exercicio_service import ExercicioService

_GIF_URL_PATTERN = re.compile(r"https?://\S+\.gif(?:\?\S*)?", re.IGNORECASE)
_NOME_JSON_PATTERN = re.compile(r'"nome"\s*:\s*"([^"]+)"')
_NOME_EM_DESTAQUE_PATTERN = re.compile(r"\*([^*]+)\*")
_PEDIDO_GIF_PATTERN = re.compile(
    r"\b(gif|anima[cç][aã]o|execu[cç][aã]o)\b", re.IGNORECASE
)
_NOME_NO_PEDIDO_GIF_PATTERN = re.compile(
    r"\bgif\s+(?:do|da|de|pro|pra|para)?\s*(.+)$", re.IGNORECASE
)
_MAX_HISTORICO_LINHAS = 30
_MAX_RESUMOS = 8
_MAX_RESUMOS_NO_CONTEXTO = 4

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
- ao mostrar instrução de exercício, priorize resumo objetivo em passos curtos
- se a instrução for longa, entregue um resumo prático e ofereça detalhes completos se o usuário pedir
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
- instrução em até 5 linhas curtas, sem cortar frase no meio
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
    """Cria e retorna a instância do agente."""
    _configurar_langsmith()

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0,
        max_output_tokens=320,
    )

    return create_react_agent(
        model=llm,
        tools=get_agent_tools(),
        prompt=SystemMessage(content=_SYSTEM_PROMPT),
    )


# Instância única do agente
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
        self._ultimo_exercicio: dict[str, dict[str, str]] = {}
        self._resumo_contexto: dict[str, list[str]] = {}

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
        recente = historico[-16:]
        contexto_fixo = self._contexto_telefone(thread_id)
        contexto_exercicio = self._contexto_ultimo_exercicio(thread_id)
        contexto_base = f"{contexto_fixo}\n{contexto_exercicio}" if contexto_exercicio else contexto_fixo
        contexto_resumo = self._contexto_resumo(thread_id)
        if contexto_resumo:
            contexto_base = f"{contexto_base}\n{contexto_resumo}"

        if not recente:
            return f"{contexto_base}\n\nUsuário: {mensagem}"

        return (
            f"{contexto_base}\n\n"
            "Histórico recente:\n"
            + "\n".join(recente)
            + "\n\nUsuário: "
            + mensagem
        )

    def _contexto_resumo(self, thread_id: str) -> str:
        resumos = self._resumo_contexto.get(thread_id, [])
        if not resumos:
            return ""

        ultimos = resumos[-_MAX_RESUMOS_NO_CONTEXTO:]
        return "Resumo acumulado da conversa:\n" + "\n".join(f"- {item}" for item in ultimos)

    @staticmethod
    def _normalizar_texto_resumo(texto: str, max_chars: int = 140) -> str:
        texto = re.sub(r"\s+", " ", (texto or "")).strip()
        if len(texto) <= max_chars:
            return texto
        return f"{texto[: max_chars - 3].rstrip()}..."

    def _resumir_linhas_historico(self, linhas: list[str]) -> str:
        itens: list[str] = []

        for linha in linhas:
            if not linha:
                continue
            if linha.startswith("Usuário:"):
                conteudo = linha.split(":", 1)[1]
                itens.append(f"U: {self._normalizar_texto_resumo(conteudo)}")
            elif linha.startswith("Assistente:"):
                conteudo = linha.split(":", 1)[1]
                itens.append(f"A: {self._normalizar_texto_resumo(conteudo)}")
            else:
                itens.append(self._normalizar_texto_resumo(linha))

        if not itens:
            return ""

        if len(itens) > 6:
            itens = itens[:2] + itens[-4:]

        return " | ".join(item for item in itens if item)

    def _compactar_historico(self, thread_id: str) -> None:
        historico = self._historico.get(thread_id, [])
        if len(historico) <= _MAX_HISTORICO_LINHAS:
            return

        antigas = historico[:-_MAX_HISTORICO_LINHAS]
        self._historico[thread_id] = historico[-_MAX_HISTORICO_LINHAS:]

        resumo = self._resumir_linhas_historico(antigas)
        if not resumo:
            return

        blocos = self._resumo_contexto.setdefault(thread_id, [])
        blocos.append(resumo)
        if len(blocos) > _MAX_RESUMOS:
            self._resumo_contexto[thread_id] = blocos[-_MAX_RESUMOS:]

    def _contexto_ultimo_exercicio(self, thread_id: str) -> str:
        estado = self._ultimo_exercicio.get(thread_id, {})
        nome = estado.get("nome")
        gif_url = estado.get("gif_url")

        if not nome and not gif_url:
            return ""

        linhas = ["Contexto de exercício recente:"]
        if nome:
            linhas.append(f"- ultimo_exercicio_citado: {nome}")
        if gif_url:
            linhas.append(f"- ultimo_gif_url: {gif_url}")
        return "\n".join(linhas)

    @staticmethod
    def _coletar_textos(valor: Any) -> list[str]:
        """Varre recursivamente estruturas para extrair textos úteis."""
        textos: list[str] = []
        pilha: list[Any] = [valor]

        while pilha:
            atual = pilha.pop()
            if atual is None:
                continue

            if isinstance(atual, str):
                textos.append(atual)
                continue

            if isinstance(atual, dict):
                pilha.extend(atual.values())
                continue

            if isinstance(atual, (list, tuple, set)):
                pilha.extend(list(atual))
                continue

            conteudo = getattr(atual, "content", None)
            if conteudo is not None:
                pilha.append(conteudo)

        return textos

    @staticmethod
    def _normalizar_nome_exercicio(nome: str) -> str:
        nome = nome.strip().strip("* ").strip()
        return re.sub(r"\s+", " ", nome)

    @staticmethod
    def _eh_pedido_gif(texto: str) -> bool:
        return bool(_PEDIDO_GIF_PATTERN.search(texto or ""))

    @staticmethod
    def _extrair_nome_do_pedido_gif(texto: str) -> str | None:
        match = _NOME_NO_PEDIDO_GIF_PATTERN.search((texto or "").strip())
        if not match:
            return None
        nome = re.sub(r"[?.!,:;]+$", "", match.group(1)).strip()
        if not nome:
            return None
        return nome

    @staticmethod
    def _extrair_gif_url(texto: str) -> str | None:
        urls = _GIF_URL_PATTERN.findall(texto or "")
        return urls[-1] if urls else None

    def _buscar_gif_por_nome(self, nome_exercicio: str) -> str | None:
        """Busca um GIF no catálogo para usar como fallback determinístico."""
        with SessionLocal() as session:
            service = ExercicioService(session)
            resultados = service.search_exercicios(nome=nome_exercicio, limite=1)
            if not resultados:
                return None
            return resultados[0].gif_url

    def _atualizar_memoria_exercicio(self, thread_id: str, resultado: dict, resposta: str) -> None:
        estado = self._ultimo_exercicio.setdefault(thread_id, {})

        textos = self._coletar_textos(resultado)
        textos.append(resposta)
        corpus = "\n".join(t for t in textos if t)

        gif_url = self._extrair_gif_url(corpus)
        if gif_url:
            estado["gif_url"] = gif_url

        nomes_json = _NOME_JSON_PATTERN.findall(corpus)
        if nomes_json:
            estado["nome"] = self._normalizar_nome_exercicio(nomes_json[-1])
            return

        nomes_md = _NOME_EM_DESTAQUE_PATTERN.findall(resposta or "")
        if nomes_md:
            estado["nome"] = self._normalizar_nome_exercicio(nomes_md[0])

    def _garantir_link_gif(self, thread_id: str, mensagem: str, resposta: str) -> str:
        if not self._eh_pedido_gif(mensagem):
            return resposta

        if self._extrair_gif_url(resposta):
            return resposta

        estado = self._ultimo_exercicio.setdefault(thread_id, {})
        gif_url = estado.get("gif_url")

        if not gif_url:
            nome_exercicio = self._extrair_nome_do_pedido_gif(mensagem) or estado.get("nome")
            if nome_exercicio:
                gif_url = self._buscar_gif_por_nome(nome_exercicio)
                if gif_url:
                    estado["nome"] = self._normalizar_nome_exercicio(nome_exercicio)
                    estado["gif_url"] = gif_url

        if not gif_url:
            return resposta

        complemento = f"Link do GIF: {gif_url}"
        return f"{resposta.strip()}\n{complemento}" if resposta.strip() else complemento

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
        self._atualizar_memoria_exercicio(thread_id, resultado, resposta)
        resposta = self._garantir_link_gif(thread_id, mensagem, resposta)

        historico = self._historico.setdefault(thread_id, [])
        historico.extend([f"Usuário: {mensagem}", f"Assistente: {resposta}"])
        self._compactar_historico(thread_id)

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
