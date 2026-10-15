from datetime import date

from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.ciclo_service import CicloService


@tool
def criar_ciclo_com_rotacao(
    usuario_id: str,
    nome: str,
    data_inicio: str,
    treino_ids: list[str],
    duracao_meses: int,
) -> dict:
    """Cria um ciclo de treino e popula as sessoes automaticamente com rotacao continua.

    Usa a meta semanal de treinos do usuario (meta_semanal_dias) para calcular
    o total de sessoes. A rotacao continua de onde parou entre semanas.

    Exemplo: treino_ids=[A, B, C, D], duracao_meses=3, meta=4 dias/semana
    -> 3 meses x 4 semanas x 4 dias = 48 sessoes
    -> sequencia: A B C D A B C D A B C D ...

    Args:
        usuario_id: ID do usuario.
        nome: Nome do ciclo (ex: 'ABCD Hipertrofia 3 meses').
        data_inicio: Data de inicio no formato ISO (YYYY-MM-DD).
        treino_ids: Lista de IDs dos treinos na ordem da rotacao (ex: [id_A, id_B, id_C, id_D]).
        duracao_meses: Duracao do ciclo em meses inteiros.
    """
    session = SessionLocal()
    try:
        try:
            data = date.fromisoformat(data_inicio)
            ciclo_service = CicloService(session)
            resultado = ciclo_service.criar_ciclo_com_rotacao(
                usuario_id=usuario_id,
                nome=nome,
                data_inicio=data,
                treino_ids=treino_ids,
                duracao_meses=duracao_meses,
            )
            return resultado
        except ValueError as e:
            return {"error": str(e)}
    finally:
        session.close()
