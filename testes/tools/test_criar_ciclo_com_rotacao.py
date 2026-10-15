"""Testes para a tool criar_ciclo_com_rotacao."""
from datetime import date

from app.schemas.treino import TreinoCreate
from app.schemas.usuario import UsuarioCreate
from app.service.ciclo_service import CicloService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService
from app.repositorio.ciclo_sessao import CicloSessaoRepositorio
from app.tools.ciclo import criar_ciclo_com_rotacao as modulo

_tel = [40_000_000_000]


def _tel_unico():
    _tel[0] += 1
    return str(_tel[0])


def _usuario(db_session):
    return UsuarioService(db_session).criar_usuario(
        UsuarioCreate(name="Rotacao Test", telefone=_tel_unico())
    )


def _treino(db_session, usuario_id, nome):
    return TreinoService(db_session).criar_treino(
        TreinoCreate(usuario_id=usuario_id, nome=nome, descricao="desc", dia_da_semana=None)
    )


def test_criar_ciclo_com_rotacao_4_treinos_1_mes(db_session):
    """4 treinos, 1 mês, meta=4 dias/semana → 16 sessões em rotação ABCDABCD..."""
    usuario = _usuario(db_session)
    treinos = [_treino(db_session, usuario.id, f"Treino {l}") for l in "ABCD"]
    ids = [t.id for t in treinos]

    svc = CicloService(db_session)
    resultado = svc.criar_ciclo_com_rotacao(
        usuario_id=usuario.id,
        nome="ABCD 1 mês",
        data_inicio=date(2027, 1, 1),
        treino_ids=ids,
        duracao_meses=1,
    )

    assert resultado["total_sessoes"] == 16  # 4 semanas × 4 dias
    assert resultado["dias_por_semana"] == 4

    sessoes = CicloSessaoRepositorio(db_session).listar_sessoes_por_ciclo(resultado["ciclo"]["id"])
    assert len(sessoes) == 16

    # Verifica rotação: sessão 1=A, 2=B, 3=C, 4=D, 5=A, ...
    for i, sessao in enumerate(sessoes):
        assert sessao.treino_id == ids[i % 4]


def test_criar_ciclo_com_rotacao_3_meses(db_session):
    """ABCD, 3 meses, meta=4 → 48 sessões."""
    usuario = _usuario(db_session)
    treinos = [_treino(db_session, usuario.id, f"Treino {l}") for l in "ABCD"]
    ids = [t.id for t in treinos]

    svc = CicloService(db_session)
    resultado = svc.criar_ciclo_com_rotacao(
        usuario_id=usuario.id,
        nome="ABCD 3 meses",
        data_inicio=date(2027, 1, 1),
        treino_ids=ids,
        duracao_meses=3,
    )

    assert resultado["total_sessoes"] == 48  # 12 semanas × 4 dias


def test_criar_ciclo_com_rotacao_via_tool(db_session, monkeypatch):
    """Tool retorna total_sessoes e ciclo com status=ativo."""
    usuario = _usuario(db_session)
    treinos = [_treino(db_session, usuario.id, f"Treino {l}") for l in "AB"]
    ids = [t.id for t in treinos]

    monkeypatch.setattr(modulo, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session.__class__, "close", lambda self: None, raising=False)

    resultado = modulo.criar_ciclo_com_rotacao.invoke({
        "usuario_id": usuario.id,
        "nome": "AB 1 mês",
        "data_inicio": "2027-01-01",
        "treino_ids": ids,
        "duracao_meses": 1,
    })

    assert resultado["ciclo"]["status"] == "ativo"
    assert resultado["total_sessoes"] == 16  # 4 semanas × 4 dias


def test_criar_ciclo_com_rotacao_treino_inexistente_retorna_erro(db_session, monkeypatch):
    """Tool retorna {"error": ...} quando treino_id não existe."""
    usuario = _usuario(db_session)

    monkeypatch.setattr(modulo, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session.__class__, "close", lambda self: None, raising=False)

    resultado = modulo.criar_ciclo_com_rotacao.invoke({
        "usuario_id": usuario.id,
        "nome": "Ciclo X",
        "data_inicio": "2027-01-01",
        "treino_ids": ["id-inexistente"],
        "duracao_meses": 1,
    })

    assert "error" in resultado
