from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ciclo_sessao import CicloSessao, StatusCicloSessao


class CicloSessaoRepositorio:
    """Repositório para operações de banco de dados relacionadas a sessões de ciclo."""

    def __init__(self, session: Session):
        self.session = session

    def criar_sessao(self, sessao: CicloSessao) -> CicloSessao:
        """Insere uma nova sessão e retorna o objeto persistido."""
        self.session.add(sessao)
        self.session.commit()
        self.session.refresh(sessao)
        return sessao

    def obter_sessao_por_id(self, sessao_id: str) -> CicloSessao | None:
        """Obtém uma sessão pelo ID."""
        stmt = select(CicloSessao).where(CicloSessao.id == sessao_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def obter_sessao_em_execucao(self, ciclo_id: str) -> CicloSessao | None:
        """Retorna a sessão com status='em_execucao', se existir."""
        stmt = select(CicloSessao).where(
            CicloSessao.ciclo_id == ciclo_id,
            CicloSessao.status == StatusCicloSessao.EM_EXECUCAO.value,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def obter_proxima_sessao(self, ciclo_id: str) -> CicloSessao | None:
        """Retorna a próxima sessão aguardando (menor numero_sessao com status='aguardando')."""
        stmt = (
            select(CicloSessao)
            .where(
                CicloSessao.ciclo_id == ciclo_id,
                CicloSessao.status == StatusCicloSessao.AGUARDANDO.value,
            )
            .order_by(CicloSessao.numero_sessao.asc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def listar_sessoes_por_ciclo(self, ciclo_id: str) -> list[CicloSessao]:
        """Lista todas as sessões de um ciclo ordenadas por numero_sessao crescente."""
        stmt = (
            select(CicloSessao)
            .where(CicloSessao.ciclo_id == ciclo_id)
            .order_by(CicloSessao.numero_sessao.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def obter_sessao_por_numero(self, ciclo_id: str, numero_sessao: int) -> CicloSessao | None:
        """Obtém uma sessão pelo ciclo e número ordinal."""
        stmt = select(CicloSessao).where(
            CicloSessao.ciclo_id == ciclo_id,
            CicloSessao.numero_sessao == numero_sessao,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def atualizar_sessao(self, sessao: CicloSessao) -> CicloSessao:
        """Persiste alterações em uma sessão existente."""
        self.session.commit()
        self.session.refresh(sessao)
        return sessao
