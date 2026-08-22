from datetime import timezone, timedelta

from langchain_core.tools import tool

from app.core import config
from app.core.database import SessionLocal
from app.service.dashboard_token_service import DashboardTokenService

_BRT = timezone(timedelta(hours=-3))


@tool
def gerar_link_dashboard(usuario_id: str, expira_em_minutos: int = 60) -> dict:
    """Gera um link temporario e seguro para o dashboard do usuario.

    O token é salvo no banco e validado no servidor — links expirados ou
    já utilizados são rejeitados automaticamente.
    """
    session = SessionLocal()
    try:
        service = DashboardTokenService(session)
        registro = service.emitir(usuario_id=usuario_id, ttl_minutos=expira_em_minutos)

        expires_brt = registro.expires_at.astimezone(_BRT)

        return {
            "url": f"{config.BASE_URL}/dashboard/view?token={registro.token}",
            "expires_at": expires_brt.strftime("%d/%m/%Y %H:%M (BRT)"),
            "expires_in_minutes": expira_em_minutos,
        }
    finally:
        session.close()
