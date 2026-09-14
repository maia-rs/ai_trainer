from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.schemas.usuario import UsuarioUpdate, UsuarioResponse
from app.service.usuario_service import UsuarioService


@tool
def atualizar_usuario(
    usuario_id: str,
    nome: str | None = None,
    telefone: str | None = None,
    meta_semanal_dias: int | None = None,
) -> dict:
    """Atualiza os dados de um usuário existente.
    
    Permite alterar nome, telefone e/ou meta de dias de treino por semana.
    Informe apenas os campos que deseja alterar.
    
    Args:
        usuario_id: ID do usuário a ser atualizado.
        nome: Novo nome do usuário (opcional).
        telefone: Novo telefone no formato (XX) XXXXX-XXXX (opcional).
        meta_semanal_dias: Meta de dias de treino por semana, entre 1 e 7 (opcional).
    """
    session = SessionLocal()
    try:
        usuario_service = UsuarioService(session)

        usuario = usuario_service.obter_usuario_por_id(usuario_id)
        if not usuario:
            return {"error": "Usuário não encontrado."}

        dados: dict = {}
        if nome is not None:
            dados["name"] = nome
        if telefone is not None:
            dados["telefone"] = telefone
        if meta_semanal_dias is not None:
            if not (1 <= meta_semanal_dias <= 7):
                return {"error": "meta_semanal_dias deve ser entre 1 e 7."}
            dados["meta_semanal_dias"] = meta_semanal_dias

        if not dados:
            return {"error": "Nenhum campo informado para atualização."}

        try:
            atualizado = usuario_service.atualizar_usuario(
                usuario_id, UsuarioUpdate(**dados)
            )
        except ValueError as e:
            return {"error": str(e)}

        return UsuarioResponse.model_validate(atualizado).model_dump(
            include={"id", "name", "telefone", "status", "meta_semanal_dias"}
        )
    finally:
        session.close()
