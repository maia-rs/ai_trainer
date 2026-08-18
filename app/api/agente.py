import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from app.schemas.agente import AgenteChatRequest, AgenteChatResponse
from app.service.agente_service import AgenteService

router = APIRouter(prefix="/agente", tags=["Agente"])


@router.get("/health")
def health_agente() -> JSONResponse:
    payload, status_code = AgenteService.verificar_health()
    return JSONResponse(content=payload, status_code=status_code)


@router.post("/chat", response_model=AgenteChatResponse)
def conversar_com_agente(payload: AgenteChatRequest) -> AgenteChatResponse:
    try:
        service = AgenteService()
        resultado = service.conversar(
            mensagem=payload.mensagem,
            thread_id=payload.thread_id,
        )
        return AgenteChatResponse(**resultado)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Erro ao executar o agente: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error
