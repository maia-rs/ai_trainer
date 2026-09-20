"""Testes de idempotência em registrar_execucao — Bug 3 (agent-resilience)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.execucao import ExecucaoCreate
from app.schemas.exercicio import ExercicioCreate
from app.schemas.treino import TreinoCreate
from app.schemas.treino_exercicio import TreinoExercicioCreate
from app.schemas.usuario import UsuarioCreate
from app.service.execucao_service import ExecucaoService
from app.service.exercicio_service import ExercicioService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _criar_usuario(db_session, nome: str, telefone: str):
    return UsuarioService(db_session).criar_usuario(
        UsuarioCreate(name=nome, telefone=telefone)
    )


def _criar_treino(db_session, usuario_id: str, nome: str = "Treino B3"):
    return TreinoService(db_session).criar_treino(
        TreinoCreate(
            usuario_id=usuario_id,
            nome=nome,
            descricao="Treino para testes de idempotência",
            dia_da_semana="Segunda-feira",
        )
    )


def _criar_exercicio(db_session, sufixo: str = "b3-1"):
    return ExercicioService(db_session).criar_exercicio(
        ExercicioCreate(
            id_externo=f"b3-exec-{sufixo}",
            nome=f"Exercicio B3 {sufixo}",
            categoria="Forca",
            rotulo="Supino",
            grupo_muscular="Peito",
            equipamento="Barra",
            instrucao="Executar com amplitude completa.",
            gif_url="https://example.com/b3.gif",
        )
    )


def _criar_treino_exercicio(db_session, treino_id: str, exercicio_id: str):
    return TreinoExercicioService(db_session).criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino_id,
            exercicio_id=exercicio_id,
            series=3,
            repeticoes=12,
            descanso=60,
        )
    )


def _payload(usuario_id: str, treino_exercicio_id: str, carga: int = 80) -> ExecucaoCreate:
    return ExecucaoCreate(
        usuario_id=usuario_id,
        treino_exercicio_id=treino_exercicio_id,
        data_execucao=datetime.now(timezone.utc) - timedelta(minutes=5),
        carga=carga,
        series=3,
        repeticoes=12,
        tempo_descanso_real=60,
        duracao_execucao=1200,
        calorias_queimadas=150,
        frequencia_cardiaca_media=120,
        observacoes="Teste idempotência",
    )


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

def test_execucao_duplicada_retorna_existente(db_session):
    """2 chamadas idênticas → mesmo id, 1 único registro no banco."""
    usuario = _criar_usuario(db_session, "Idem User 1", "11920000001")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "b3a")
    te = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    service = ExecucaoService(db_session)
    resp1 = service.registrar_execucao(_payload(usuario.id, te.id))
    resp2 = service.registrar_execucao(_payload(usuario.id, te.id))

    assert resp1.id == resp2.id
    # Apenas 1 registro deve existir no banco
    execucoes = service.listar_execucoes_por_usuario(usuario.id)
    assert len(execucoes) == 1


def test_execucao_carga_diferente_insere_nova(db_session):
    """Carga diferente → 2 registros distintos."""
    usuario = _criar_usuario(db_session, "Idem User 2", "11920000002")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "b3b")
    te = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    service = ExecucaoService(db_session)
    resp1 = service.registrar_execucao(_payload(usuario.id, te.id, carga=80))
    resp2 = service.registrar_execucao(_payload(usuario.id, te.id, carga=90))

    assert resp1.id != resp2.id
    execucoes = service.listar_execucoes_por_usuario(usuario.id)
    assert len(execucoes) == 2


def test_execucao_treino_exercicio_diferente_insere_nova(db_session):
    """treino_exercicio_id diferente → 2 registros distintos."""
    usuario = _criar_usuario(db_session, "Idem User 3", "11920000003")
    treino = _criar_treino(db_session, usuario.id)
    exercicio1 = _criar_exercicio(db_session, "b3c1")
    exercicio2 = _criar_exercicio(db_session, "b3c2")
    te1 = _criar_treino_exercicio(db_session, treino.id, exercicio1.id)
    te2 = _criar_treino_exercicio(db_session, treino.id, exercicio2.id)

    service = ExecucaoService(db_session)
    resp1 = service.registrar_execucao(_payload(usuario.id, te1.id))
    resp2 = service.registrar_execucao(_payload(usuario.id, te2.id))

    assert resp1.id != resp2.id
    execucoes = service.listar_execucoes_por_usuario(usuario.id)
    assert len(execucoes) == 2


def test_execucao_dedup_desabilitada_com_zero(db_session, monkeypatch):
    """Com EXECUCAO_DEDUP_JANELA_MINUTOS=0, 2 chamadas idênticas criam 2 registros."""
    import app.service.execucao_service as svc_module

    monkeypatch.setattr(svc_module, "EXECUCAO_DEDUP_JANELA_MINUTOS", 0)

    usuario = _criar_usuario(db_session, "Idem User 4", "11920000004")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "b3d")
    te = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    service = ExecucaoService(db_session)
    resp1 = service.registrar_execucao(_payload(usuario.id, te.id))
    resp2 = service.registrar_execucao(_payload(usuario.id, te.id))

    assert resp1.id != resp2.id
    execucoes = service.listar_execucoes_por_usuario(usuario.id)
    assert len(execucoes) == 2


def test_validacoes_existentes_preservadas(db_session):
    """Carga negativa ainda deve lançar ValueError (validações anteriores intactas)."""
    usuario = _criar_usuario(db_session, "Idem User 5", "11920000005")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "b3e")
    te = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    payload = _payload(usuario.id, te.id)
    payload.carga = -5

    with pytest.raises(ValueError, match="carga deve ser maior ou igual a zero"):
        ExecucaoService(db_session).registrar_execucao(payload)
