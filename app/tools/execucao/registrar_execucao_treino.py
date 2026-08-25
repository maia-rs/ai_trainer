from datetime import datetime, timezone

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.schemas.execucao import ExecucaoCreate
from app.service.execucao_service import ExecucaoService


@tool(handle_tool_error=True)
def registrar_execucao_treino(
    usuario_id: str,
    treino_exercicio_id: str,
    carga: int,
    repeticoes: int,
    series: int,
    duracao: int,
    tempo_descanso: int = 60,
    calorias_queimadas: int = 0,
    frequencia_cardiaca_media: int = 0,
    observacoes: str | None = None,
    data_execucao_iso: str | None = None,
) -> dict:
    """Registra a execucao de um exercicio em um treino."""

    session = SessionLocal()

    try:
        execucao_service = ExecucaoService(session)

        try:
            if data_execucao_iso:
                data_execucao = datetime.fromisoformat(data_execucao_iso)
            else:
                data_execucao = datetime.now(timezone.utc)

            payload = ExecucaoCreate(
                usuario_id=usuario_id,
                treino_exercicio_id=treino_exercicio_id,
                data_execucao=data_execucao,
                carga=carga,
                series=series,
                repeticoes=repeticoes,
                tempo_descanso_real=tempo_descanso,
                duracao_execucao=duracao,
                calorias_queimadas=calorias_queimadas,
                frequencia_cardiaca_media=frequencia_cardiaca_media,
                observacoes=observacoes,
            )
            execucao = execucao_service.registrar_execucao(payload)
            return execucao.model_dump()
        except ValueError as e:
            return {"error": str(e)}

    finally:
        session.close()