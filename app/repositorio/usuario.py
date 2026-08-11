from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.tipos.telefone_tipo import TelefoneValue # Importar TelefoneValue

class UsuarioRepositorio:
    """Classe de repositório para operações de banco de dados relacionadas a usuários."""

    def __init__(self, session: Session):
        self.session = session

    def criar_usuario(self, usuario: Usuario) -> Usuario:
        """Cria um novo usuário no banco de dados."""
        self.session.add(usuario)
        self.session.commit()
        self.session.refresh(usuario)
        return usuario

    def obter_usuario_por_id(self, usuario_id: str) -> Usuario | None:
        """Obtém um usuário pelo ID."""
        stmt = select(Usuario).where(Usuario.id == usuario_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def obter_usuario_por_telefone(self, telefone: str) -> Usuario | None:
        """Obtém um usuário pelo telefone."""
        # Converte a string de telefone para um objeto TelefoneValue para a comparação
        stmt = select(Usuario).where(Usuario.telefone == TelefoneValue(telefone))
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def atualizar_usuario(self, usuario: Usuario) -> Usuario:
        """Atualiza um usuário existente no banco de dados."""
        self.session.commit()
        self.session.refresh(usuario)
        return usuario

    def deletar_usuario(self, usuario: Usuario) -> None:
        """Deleta um usuário do banco de dados."""
        self.session.delete(usuario)
        self.session.commit()