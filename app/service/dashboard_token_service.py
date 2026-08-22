from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from sqlalchemy.orm import Session

from app.models.dashboard_token import DashboardToken
from app.repositorio.dashboard_token import DashboardTokenRepositorio


class DashboardTokenService:
    """Serviço para emissão e validação de tokens de acesso ao dashboard."""

    def __init__(self, session: Session):
        self.repo = DashboardTokenRepositorio(session)

    def emitir(self, usuario_id: str, ttl_minutos: int = 60) -> DashboardToken:
        """Gera e persiste um novo token para o usuário."""
        token = DashboardToken(
            token=token_urlsafe(32),
            usuario_id=usuario_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=max(ttl_minutos, 1)),
            used=False,
        )
        return self.repo.criar(token)

    def validar(self, token_str: str) -> DashboardToken:
        """
        Valida o token e retorna o objeto se válido.
        Lança ValueError em caso de token inválido, expirado ou já usado.
        """
        registro = self.repo.obter_por_token(token_str)

        if not registro:
            raise ValueError("Token inválido.")

        if registro.used:
            raise ValueError("Token já utilizado.")

        # SQLite devolve datetime sem tzinfo — normaliza para UTC antes de comparar
        expires_at = registro.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > expires_at:
            raise ValueError("Token expirado.")

        return registro
