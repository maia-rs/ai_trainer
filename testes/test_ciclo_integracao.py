"""Testes de integração ponta a ponta para a feature de Ciclos de Treino.

Cobre requisitos: 1.4, 5.3, 5.4, 6.4, 7.1, 7.3, 9.2, 9.3, 9.4, 10.1, 10.4
"""
from datetime import date

from app.schemas.treino import TreinoCreate
from app.schemas.usuario import UsuarioCreate
from app.service.ciclo_service import CicloService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService
from app.repositorio.ciclo import CicloRepositorio
from app.tools.ciclo import criar_ciclo as criar_ciclo_module
from app.tools.ciclo import adicionar_sessao_ciclo as adicionar_sessao_module
from app.tools.ciclo import obter_proxima_sessao as obter_proxima_module
from app.tools.ciclo import obter_progresso_ciclo as obter_progresso_module
from app.tools.treino import obter_treino_do_dia as obter_treino_do_dia_module


# ── Helpers ────────────────────────────────────────────────────────────────────

_tel_counter = [30_000_000_000]


def _tel():
    _tel_counter[0] += 1
    return str(_tel_counter[0])


def _usuario(db_session):
    return UsuarioService(db_session).criar_usuario(
        UsuarioCreate(name="Integracao", telefone=_tel())
    )


def _treino(db_session, usuario_id, nome="Treino Int", dia=None):
    return TreinoService(db_session).criar_treino(
        TreinoCreate(usuario_id=usuario_id, nome=nome, descricao="desc", dia_da_semana=dia)
    )


def _ciclo(db_session, usuario_id):
    return CicloService(db_session).criar_ciclo(usuario_id, "Ciclo Int", date(2027, 1, 1))


# ── Testes de integração via service ──────────────────────────────────────────


def test_fluxo_completo_criar_concluir_todas_sessoes(db_session):
    """Req 6.4, 5.4 — criar ciclo → 5 sessões → concluir todas → ciclo=concluido."""
    usuario = _usuario(db_session)
    treino = _treino(db_session, usuario.id)
    ciclo = _ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    sessoes = [svc.adicionar_sessao(ciclo.id, n, treino.id) for n in range(1, 6)]

    for sessao in sessoes:
        svc.concluir_sessao(sessao.id)

    ciclo_final = CicloRepositorio(db_session).obter_ciclo_por_id(ciclo.id)
    assert ciclo_final.status == "concluido"
    assert svc.obter_proxima_sessao(usuario.id) is None


def test_usuario_sem_ciclo_proxima_sessao_retorna_none(db_session):
    """Req 5.3 — usuário sem ciclo ativo: obter_proxima_sessao retorna None."""
    usuario = _usuario(db_session)
    svc = CicloService(db_session)
    assert svc.obter_proxima_sessao(usuario.id) is None


def test_ciclo_60_sessoes_metade_concluida(db_session):
    """Req 7.1, 7.3 — ciclo de 60 sessões com 30 concluídas → percentual=50.0."""
    usuario = _usuario(db_session)
    treino = _treino(db_session, usuario.id)
    ciclo = _ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    sessoes = [svc.adicionar_sessao(ciclo.id, n, treino.id) for n in range(1, 61)]

    for i in range(30):
        svc.concluir_sessao(sessoes[i].id)

    progresso = svc.obter_progresso_ciclo(ciclo.id)
    assert progresso["sessoes_concluidas"] == 30
    assert progresso["total_sessoes"] == 60
    assert progresso["percentual_conclusao"] == 50.0


def test_treino_sem_dia_da_semana_usado_em_ciclo(db_session):
    """Req 1.4 — treino criado com dia_da_semana=None pode ser usado em ciclo sem erro."""
    usuario = _usuario(db_session)
    treino = _treino(db_session, usuario.id, dia=None)
    ciclo = _ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    sessao = svc.adicionar_sessao(ciclo.id, 1, treino.id)
    assert sessao.treino_id == treino.id


def test_obter_treino_do_dia_com_ciclo_ativo_retorna_fonte_ciclo(db_session):
    """Req 10.1 — com ciclo ativo, obter_treino_do_dia retorna fonte='ciclo'."""
    usuario = _usuario(db_session)
    treino = _treino(db_session, usuario.id)
    ciclo = _ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    svc.adicionar_sessao(ciclo.id, 1, treino.id)

    resultado = svc.obter_treino_do_dia(usuario.id)
    assert resultado["fonte"] == "ciclo"
    assert "ciclo_sessao_id" in resultado


def test_obter_treino_do_dia_sem_ciclo_retorna_fonte_dia_semana(db_session):
    """Req 10.4 — sem ciclo ativo, obter_treino_do_dia retorna fonte='dia_semana'."""
    usuario = _usuario(db_session)

    resultado = CicloService(db_session).obter_treino_do_dia(usuario.id)
    assert resultado["fonte"] == "dia_semana"


# ── Testes de integração via tools ────────────────────────────────────────────


class _DummySession:
    def close(self):
        pass


def test_fluxo_via_tools(db_session, monkeypatch):
    """Req 9.2–9.4 — fluxo criar_ciclo → adicionar_sessao_ciclo × N → obter_proxima_sessao."""
    usuario = _usuario(db_session)
    treino = _treino(db_session, usuario.id)

    # Injeta a sessão de teste nas tools via monkeypatch
    monkeypatch.setattr(criar_ciclo_module, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(adicionar_sessao_module, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(obter_proxima_module, "SessionLocal", lambda: db_session)

    # Patch close para não fechar a sessão de teste
    monkeypatch.setattr(db_session.__class__, "close", lambda self: None, raising=False)

    ciclo_resp = criar_ciclo_module.criar_ciclo.invoke({
        "usuario_id": usuario.id,
        "nome": "Ciclo Via Tool",
        "data_inicio": "2027-06-01",
    })
    assert ciclo_resp["status"] == "ativo"

    for n in range(1, 4):
        sessao_resp = adicionar_sessao_module.adicionar_sessao_ciclo.invoke({
            "ciclo_id": ciclo_resp["id"],
            "numero_sessao": n,
            "treino_id": treino.id,
        })
        assert sessao_resp["numero_sessao"] == n

    proxima_resp = obter_proxima_module.obter_proxima_sessao.invoke({"usuario_id": usuario.id})
    assert proxima_resp["proxima_sessao"] is not None
    assert proxima_resp["proxima_sessao"]["numero_sessao"] == 1
    assert proxima_resp["proxima_sessao"]["treino_nome"] == treino.nome


def test_obter_progresso_via_tool(db_session, monkeypatch):
    """Req 9.7 — obter_progresso_ciclo tool retorna métricas corretas no fluxo integrado."""
    usuario = _usuario(db_session)
    treino = _treino(db_session, usuario.id)
    ciclo = _ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    sessoes = [svc.adicionar_sessao(ciclo.id, n, treino.id) for n in range(1, 5)]
    svc.concluir_sessao(sessoes[0].id)
    svc.concluir_sessao(sessoes[1].id)

    monkeypatch.setattr(obter_progresso_module, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session.__class__, "close", lambda self: None, raising=False)

    resultado = obter_progresso_module.obter_progresso_ciclo.invoke({"ciclo_id": ciclo.id})
    assert resultado["sessoes_concluidas"] == 2
    assert resultado["total_sessoes"] == 4
    assert resultado["percentual_conclusao"] == 50.0


def test_obter_treino_do_dia_tool_com_ciclo(db_session, monkeypatch):
    """Req 10.1 — tool obter_treino_do_dia retorna fonte='ciclo' quando há ciclo ativo."""
    usuario = _usuario(db_session)
    treino = _treino(db_session, usuario.id)
    ciclo = _ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    svc.adicionar_sessao(ciclo.id, 1, treino.id)

    monkeypatch.setattr(obter_treino_do_dia_module, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session.__class__, "close", lambda self: None, raising=False)

    # Patch TreinoExercicioService para não quebrar na ausência de exercícios
    class FakeTreinoExSvc:
        def __init__(self, session):
            pass
        def listar_treinos_exercicios_por_treino(self, tid):
            return []
        def obter_exercicios_por_treino(self, tid):
            return []

    monkeypatch.setattr(obter_treino_do_dia_module, "TreinoExercicioService", FakeTreinoExSvc)

    resultado = obter_treino_do_dia_module.obter_treino_do_dia.invoke({"usuario_id": usuario.id})
    assert resultado["fonte"] == "ciclo"
    assert resultado.get("ciclo_sessao_id") is not None
