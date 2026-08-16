from langchain_core.tools import tool

from app.service.usuario_service import UsuarioService
from app.core.database import SessionLocal
from app.schemas.usuario import UsuarioResponse


@tool
def consultar_usuario(
    telefone: str) -> dict:

    """Consulta um usuário pelo telefone no sistema. Caso não exista, sugere a criação de um novo usuário."""

    session = SessionLocal()
    try:
        usuario_service = UsuarioService(session)
        try:
            usuario = usuario_service.obter_usuario_por_telefone(telefone=telefone)
            if not usuario:
                return {"message": "Usuário não encontrado. Deseja criar um novo usuário?"}

            return UsuarioResponse.model_validate(usuario).model_dump(
                include={"id", "name", "telefone", "status"}
            )
        except ValueError as e:
            return {"error": str(e)}
    finally:
        session.close()