from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ciclo import Ciclo, StatusCiclo


class CicloRepositorio:
    """Repositório para operações de banco de dados relacionadas a ciclos de treino."""

    def __init__(self, session: Session):
        self.session = session

    def criar_ciclo(self, ciclo: Ciclo) -> Ciclo:
        """Insere um novo ciclo e retorna o objeto persistido."""
        self.session.add(ciclo)
        self.session.commit()
        self.session.refresh(ciclo)
        return ciclo

    def obter_ciclo_por_id(self, ciclo_id: str) -> Ciclo | None:
        """Obtém um ciclo pelo ID."""
        stmt = select(Ciclo).where(Ciclo.id == ciclo_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def obter_ciclo_ativo_por_usuario(self, usuario_id: str) -> Ciclo | None:
        """Retorna o ciclo com status 'ativo' do usuário, se existir."""
        stmt = (
            select(Ciclo)
            .where(Ciclo.usuario_id == usuario_id, Ciclo.status == StatusCiclo.ATIVO.value)
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def listar_ciclos_por_usuario(self, usuario_id: str) -> list[Ciclo]:
        """Lista todos os ciclos do usuário ordenados por data_inicio decrescente."""
        stmt = (
            select(Ciclo)
            .where(Ciclo.usuario_id == usuario_id)
            .order_by(Ciclo.data_inicio.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def atualizar_ciclo(self, ciclo: Ciclo) -> Ciclo:
        """Persiste alterações em um ciclo existente."""
        self.session.commit()
        self.session.refresh(ciclo)
        return ciclo
