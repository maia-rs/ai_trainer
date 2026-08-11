from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.treino import Treino, StatusTreino


class TreinoRepositorio:
    """Classe de repositório para operações de banco de dados relacionadas a treinos."""

    def __init__(self, session: Session):
        self.session = session

    def criar_treino(self, treino: Treino) -> Treino:
        """Cria um novo treino no banco de dados."""
        self.session.add(treino)
        self.session.commit()
        self.session.refresh(treino)
        return treino

    def obter_treino_por_id(self, treino_id: str) -> Treino | None:
        """Obtém um treino pelo ID."""
        stmt = select(Treino).where(Treino.id == treino_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def obter_treinos_por_usuario(self, usuario_id: str) -> list[Treino]:
        """Obtém todos os treinos de um usuário."""
        stmt = select(Treino).where(Treino.usuario_id == usuario_id)
        result = self.session.execute(stmt).scalars().all()
        return result

    def obter_treinos_ativos_por_usuario(self, usuario_id: str) -> list[Treino]:
        """Obtém todos os treinos ativos de um usuário."""
        stmt = select(Treino).where(
            Treino.usuario_id == usuario_id,
            Treino.status == StatusTreino.ATIVO.value
        )
        result = self.session.execute(stmt).scalars().all()
        return result

    def obter_treinos_hoje_por_usuario(self, usuario_id: str) -> list[Treino]:
        """Obtém todos os treinos de hoje de um usuário."""
        stmt = select(Treino).where(
            Treino.usuario_id == usuario_id,
            Treino.data == datetime.utcnow().date()
        )
        result = self.session.execute(stmt).scalars().all()
        return result

    def atualizar_treino(self, treino: Treino) -> Treino:
        """Atualiza um treino existente no banco de dados."""
        self.session.commit()
        self.session.refresh(treino)
        return treino

    def desativar_treino(self, treino: Treino) -> Treino:
        """Desativa um treino existente no banco de dados."""
        treino.status = StatusTreino.INATIVO.value
        self.session.commit()
        self.session.refresh(treino)
        return treino