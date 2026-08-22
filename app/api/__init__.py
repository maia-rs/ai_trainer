from app.api.agente import router as agente_router
from app.api.dashboard import router as dashboard_router
from app.api.whatsapp import router as whatsapp_router

__all__ = ["dashboard_router", "agente_router", "whatsapp_router"]