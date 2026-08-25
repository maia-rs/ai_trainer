from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.avaliacao_service import AvaliacaoService


@tool(handle_tool_error=True)
def obter_avaliacao_fisica(usuario_id: str, somente_ultima: bool = True) -> dict:
    """Retorna a avaliacao fisica de um usuario."""

    session = SessionLocal()

    try:
        avaliacao_service = AvaliacaoService(session)

        try:
            if somente_ultima:
                avaliacao = avaliacao_service.obter_ultima_avaliacao_por_usuario(usuario_id)
                return {"item": avaliacao.model_dump()} if avaliacao else {"item": None}

            avaliacoes = avaliacao_service.listar_avaliacoes_por_usuario(usuario_id)
            return {
                "count": len(avaliacoes),
                "items": [item.model_dump() for item in avaliacoes],
            }
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()