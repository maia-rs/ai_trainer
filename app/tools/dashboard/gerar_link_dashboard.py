from datetime import datetime, timedelta, timezone
from uuid import uuid4

from langchain_core.tools import tool


@tool
def gerar_link_dashboard(usuario_id: str, expira_em_minutos: int = 60) -> dict:
    """Gera um link temporario para o dashboard do usuario."""

    ttl = max(expira_em_minutos, 1)
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=ttl)
    token = uuid4().hex

    return {
        "url": f"https://aitrainer.local/dashboard/{usuario_id}?token={token}",
        "expires_at": expira_em.isoformat(),
        "expires_in_minutes": ttl,
    }