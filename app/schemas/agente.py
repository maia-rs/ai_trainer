from pydantic import BaseModel, Field


class AgenteChatRequest(BaseModel):
    """Payload para interacao com o agente."""

    mensagem: str = Field(..., min_length=1, description="Mensagem enviada para o agente")
    thread_id: str = Field(
        ...,
        min_length=1,
        description="Identificador da conversa — use o usuario_id ou telefone do usuário para manter o contexto entre mensagens",
    )


class AgenteChatResponse(BaseModel):
    """Resposta padrao da API de agente."""

    thread_id: str = Field(..., description="Identificador da conversa")
    model: str = Field(..., description="Modelo configurado no provedor")
    resposta: str = Field(..., description="Resposta final gerada pelo agente")
