from app.core.database import SessionLocal
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate,UsuarioResponse
from app.repositorio.usuario import UsuarioRepositorio
from app.models.usuario import Usuario, StatusUsuario
from app.tipos.telefone_tipo import TelefoneValue
from sqlalchemy.orm import Session

class UsuarioService:
    """Classe de serviço para operações relacionadas a usuários."""

    def __init__(self, session: Session):
        self.usuario_repositorio = UsuarioRepositorio(session)

    def criar_usuario(self, usuario_create: UsuarioCreate) -> UsuarioResponse:
        """Cria um novo usuário."""
        dados = usuario_create.model_dump()
        dados["telefone"] = TelefoneValue(dados["telefone"])
        usuario = Usuario(**dados)
        #checa se o telefone já existe
        existing_usuario = self.usuario_repositorio.obter_usuario_por_telefone(str(usuario.telefone))
        if existing_usuario:
            raise ValueError("Telefone já cadastrado.")
        else:
            return UsuarioResponse.model_validate(self.usuario_repositorio.criar_usuario(usuario))

    def obter_usuario_por_id(self, usuario_id: str) -> UsuarioResponse | None:
        """Obtém um usuário pelo ID."""
        usuario = self.usuario_repositorio.obter_usuario_por_id(usuario_id)
        return UsuarioResponse.model_validate(usuario) if usuario else None

    def obter_usuario_por_telefone(self, telefone: str) -> UsuarioResponse | None:
        """Obtém um usuário pelo telefone."""
        usuario = self.usuario_repositorio.obter_usuario_por_telefone(telefone)
        return UsuarioResponse.model_validate(usuario) if usuario else None

    def atualizar_usuario(self, usuario_id: str, usuario_update: UsuarioUpdate) -> UsuarioResponse | None:
        """Atualiza um usuário existente."""
        usuario = self.usuario_repositorio.obter_usuario_por_id(usuario_id)
        if not usuario:
            return None

        for key, value in usuario_update.model_dump(exclude_unset=True).items():
            if key == "telefone" and value is not None:
                telefone = TelefoneValue(value)
                existente = self.usuario_repositorio.obter_usuario_por_telefone(str(telefone))
                if existente and existente.id != usuario_id:
                    raise ValueError("Telefone já cadastrado.")
                setattr(usuario, key, telefone)
                continue
            setattr(usuario, key, value)

        return UsuarioResponse.model_validate(self.usuario_repositorio.atualizar_usuario(usuario))

    def desativar_usuario(self, usuario_id: str) -> UsuarioResponse | None:
        """Desativa um usuário existente."""
        usuario = self.usuario_repositorio.obter_usuario_por_id(usuario_id)
        if not usuario:
            return None
        usuario.status = StatusUsuario.INATIVO.value
        return UsuarioResponse.model_validate(self.usuario_repositorio.atualizar_usuario(usuario))

    def deletar_usuario(self, usuario_id: str) -> bool:
        """Deleta um usuário pelo ID."""
        usuario = self.usuario_repositorio.obter_usuario_por_id(usuario_id)
        if not usuario:
            return False
        self.usuario_repositorio.deletar_usuario(usuario)
        return True


if __name__ == "__main__":
    # Teste local: cria o usuário caso ainda não exista.
    with SessionLocal() as session:
        usuario_service = UsuarioService(session)
        novo_usuario = UsuarioCreate(
            name="Rodrigo Maia",
            telefone="11999999999"
        )

        usuario = usuario_service.obter_usuario_por_id("ea9b6645-18a7-4064-bda4-d91076645bcc")  
        if usuario:
            print("Usuário já existe:")
            print(usuario.model_dump_json(indent=2))
        else:
            criado = usuario_service.criar_usuario(novo_usuario)
            print("Usuário criado:")
            print(criado.model_dump_json(indent=2))