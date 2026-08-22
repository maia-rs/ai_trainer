from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dashboard_token import DashboardToken


class DashboardTokenRepositorio:
    """Repositório para tokens de acesso ao dashboard."""

    def __init__(self, session: Session):
        self.session = session

    def criar(self, token: DashboardToken) -> DashboardToken:
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)
        return token

    def obter_por_token(self, token: str) -> DashboardToken | None:
        stmt = select(DashboardToken).where(DashboardToken.token == token)
        return self.session.execute(stmt).scalar_one_or_none()

    def marcar_usado(self, token: DashboardToken) -> None:
        token.used = True
        self.session.commit()

    def deletar_expirados(self) -> int:
        """Remove tokens expirados. Retorna a quantidade deletada."""
        agora = datetime.now(timezone.utc)
        stmt = select(DashboardToken).where(DashboardToken.expires_at < agora)
        expirados = self.session.execute(stmt).scalars().all()
        for t in expirados:
            self.session.delete(t)
        self.session.commit()
        return len(expirados)
