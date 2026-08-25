from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.avaliacao_service import AvaliacaoService


@tool
def obter_historico_avaliacao_fisica(usuario_id: str) -> dict:
    """Retorna o historico de avaliacoes fisicas do usuario."""

    session = SessionLocal()

    try:
        avaliacao_service = AvaliacaoService(session)

        try:
            avaliacoes = avaliacao_service.listar_avaliacoes_por_usuario(usuario_id)
            return {
                "count": len(avaliacoes),
                "items": [item.model_dump() for item in avaliacoes],
            }
        except Exception as e:
                # Captura QUALQUER exceção para sempre responder com ToolMessage
                    return {"status": "erro", "mensagem": f"Erro interno ao obter histórico de avaliações: {str(e)}"}
        

    finally:
        session.close()