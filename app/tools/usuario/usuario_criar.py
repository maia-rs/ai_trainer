from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.schemas.usuario import UsuarioCreate
from app.service.usuario_service import UsuarioService
from app.schemas.usuario import UsuarioResponse

@tool
def criar_usuario(
    nome: str,
    telefone: str
) -> dict:
    """Cria um novo usuário no sistema."""

    session = SessionLocal()

    try:
        usuario_service = UsuarioService(session)

        try:
            # Corrigido: Usar 'name' em vez de 'nome' para o esquema Pydantic
            usuario_create = UsuarioCreate(
                name=nome,
                telefone=telefone
            )

            usuario = usuario_service.criar_usuario(usuario_create)
            # Utiliza o UsuarioResponse para garantir consistência e mapeamento correto
            return UsuarioResponse.model_validate(usuario).model_dump(
                include={"id", "name", "telefone", "status"}
            )
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()