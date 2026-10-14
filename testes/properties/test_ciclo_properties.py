"""Testes de propriedade para a feature de Ciclos de Treino.

Cada propriedade valida um invariante formal do sistema usando Hypothesis.
A sessão de banco é criada internamente em cada teste para compatibilidade
com Hypothesis (que não reseta fixtures function-scoped entre exemplos).

Feature: training-cycles
"""
import random
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (  # noqa: F401 — registra tabelas no metadata
    avaliacao_fisica,
    ciclo,
    ciclo_sessao,
    dashboard_token,
    execucao,
    exercicio,
    mensagem_processada,
    treino,
    treino_exercicio,
    usuario,
)
from app.repositorio.ciclo import CicloRepositorio
from app.repositorio.ciclo_sessao import CicloSessaoRepositorio
from app.schemas.treino import TreinoCreate
from app.schemas.usuario import UsuarioCreate
from app.service.ciclo_service import CicloService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService

# Banco isolado para os testes de propriedade
_PROP_DB = Path(__file__).resolve().parent.parent / "test_properties.db"
_PROP_ENGINE = create_engine(
    f"sqlite:///{_PROP_DB}",
    connect_args={"check_same_thread": False},
)
_PropSession = sessionmaker(bind=_PROP_ENGINE, autoflush=False, autocommit=False)

# Contador de telefone único para evitar colisões entre exemplos gerados
_telefone_counter = [20_000_000_000]


def _telefone_unico():
    _telefone_counter[0] += 1
    return str(_telefone_counter[0])


@contextmanager
def _fresh_db():
    """Recria o schema e abre uma sessão limpa para cada exemplo."""
    Base.metadata.drop_all(bind=_PROP_ENGINE)
    Base.metadata.create_all(bind=_PROP_ENGINE)
    session = _PropSession()
    try:
        yield session
    finally:
        session.close()


def _criar_usuario(session):
    return UsuarioService(session).criar_usuario(
        UsuarioCreate(name="Prop Test", telefone=_telefone_unico())
    )


def _criar_treino(session, usuario_id, nome="Treino Prop"):
    return TreinoService(session).criar_treino(
        TreinoCreate(
            usuario_id=usuario_id,
            nome=(nome or "T")[:100],
            descricao="desc",
            dia_da_semana=None,
        )
    )


def _criar_ciclo(session, usuario_id, nome="Ciclo Prop", data_inicio=None):
    if data_inicio is None:
        data_inicio = date(2027, 1, 1)
    return CicloService(session).criar_ciclo(usuario_id, nome, data_inicio)


# ── Property 1 ────────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 1: round-trip de dia_da_semana nullable


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(dia=st.one_of(st.none(), st.text(min_size=1, max_size=20)))
def test_property_1_round_trip_dia_da_semana(dia):
    """Req 1.1, 1.4, 1.5 — dia_da_semana lido de volta deve ser igual ao inserido."""
    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        treino_obj = TreinoService(session).criar_treino(
            TreinoCreate(
                usuario_id=usuario.id,
                nome="Treino P1",
                descricao="desc",
                dia_da_semana=dia,
            )
        )
        recuperado = TreinoService(session).obter_treino_por_id(treino_obj.id)
        assert recuperado.dia_da_semana == dia


# ── Property 2 ────────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 2: unicidade de (ciclo_id, numero_sessao)


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(numero=st.integers(min_value=1, max_value=100))
def test_property_2_unicidade_ciclo_sessao(numero):
    """Req 2.3, 4.4 — inserir (ciclo_id, numero_sessao) duplicado lança ValueError."""
    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        treino_obj = _criar_treino(session, usuario.id)
        ciclo_obj = _criar_ciclo(session, usuario.id)

        svc = CicloService(session)
        svc.adicionar_sessao(ciclo_obj.id, numero, treino_obj.id)

        with pytest.raises(ValueError):
            svc.adicionar_sessao(ciclo_obj.id, numero, treino_obj.id)


# ── Property 3 ────────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 3: criação de ciclo sempre retorna status=ativo


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(
    nome=st.text(min_size=1, max_size=100),
    data_inicio=st.dates(min_value=date(2020, 1, 1), max_value=date(2040, 12, 31)),
)
def test_property_3_criar_ciclo_status_ativo(nome, data_inicio):
    """Req 3.1 — qualquer ciclo criado com dados válidos tem status=ativo."""
    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        ciclo_obj = CicloService(session).criar_ciclo(usuario.id, nome, data_inicio)
        assert ciclo_obj.status == "ativo"


# ── Property 4 ────────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 4: invariante de ciclo único ativo por usuário


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(
    nome_extra=st.text(min_size=1, max_size=100),
    data_extra=st.dates(min_value=date(2020, 1, 1), max_value=date(2040, 12, 31)),
)
def test_property_4_ciclo_unico_ativo_por_usuario(nome_extra, data_extra):
    """Req 3.3 — criar segundo ciclo ativo sempre lança ValueError."""
    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        _criar_ciclo(session, usuario.id)

        with pytest.raises(ValueError):
            CicloService(session).criar_ciclo(usuario.id, nome_extra, data_extra)


# ── Property 5 ────────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 5: sessões em qualquer permutação são aceitas


@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(total=st.integers(min_value=2, max_value=10))
def test_property_5_sessoes_qualquer_ordem(total):
    """Req 4.5 — inserir N sessões em qualquer ordem deve sempre ter sucesso."""
    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        treino_obj = _criar_treino(session, usuario.id)
        ciclo_obj = _criar_ciclo(session, usuario.id)

        numeros = list(range(1, total + 1))
        random.shuffle(numeros)

        svc = CicloService(session)
        for n in numeros:
            svc.adicionar_sessao(ciclo_obj.id, n, treino_obj.id)

        sessoes = CicloSessaoRepositorio(session).listar_sessoes_por_ciclo(ciclo_obj.id)
        assert len(sessoes) == total


# ── Property 6 ────────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 6: proxima_sessao é sempre a de menor numero_sessao pendente


@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(total=st.integers(min_value=2, max_value=20))
def test_property_6_proxima_sessao_menor_numero(total):
    """Req 5.1, 5.2, 11.1, 11.2 — próxima sessão é sempre a de menor numero_sessao pendente."""
    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        treino_obj = _criar_treino(session, usuario.id)
        ciclo_obj = _criar_ciclo(session, usuario.id)

        svc = CicloService(session)
        for n in range(1, total + 1):
            svc.adicionar_sessao(ciclo_obj.id, n, treino_obj.id)

        for esperado in range(1, total + 1):
            proxima = svc.obter_proxima_sessao(usuario.id)
            assert proxima is not None
            assert proxima["numero_sessao"] == esperado
            svc.concluir_sessao(proxima["ciclo_sessao_id"])


# ── Property 7 ────────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 7: obter_proxima_sessao é idempotente


@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(n_consultas=st.integers(min_value=1, max_value=20))
def test_property_7_idempotencia_proxima_sessao(n_consultas):
    """Req 11.3 — N chamadas sem concluir retornam sempre o mesmo ciclo_sessao_id."""
    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        treino_obj = _criar_treino(session, usuario.id)
        ciclo_obj = _criar_ciclo(session, usuario.id)

        svc = CicloService(session)
        for n in range(1, 4):
            svc.adicionar_sessao(ciclo_obj.id, n, treino_obj.id)

        ids = {svc.obter_proxima_sessao(usuario.id)["ciclo_sessao_id"] for _ in range(n_consultas)}
        assert len(ids) == 1


# ── Property 8 ────────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 8: sequência de numero_sessao cresce estritamente


@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(total=st.integers(min_value=2, max_value=20))
def test_property_8_sequencia_crescente(total):
    """Req 11.4 — sequência de numero_sessao após conclusões deve ser estritamente crescente."""
    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        treino_obj = _criar_treino(session, usuario.id)
        ciclo_obj = _criar_ciclo(session, usuario.id)

        svc = CicloService(session)
        for n in range(1, total + 1):
            svc.adicionar_sessao(ciclo_obj.id, n, treino_obj.id)

        numeros = []
        while True:
            proxima = svc.obter_proxima_sessao(usuario.id)
            if proxima is None:
                break
            numeros.append(proxima["numero_sessao"])
            svc.concluir_sessao(proxima["ciclo_sessao_id"])

        for i in range(len(numeros) - 1):
            assert numeros[i] < numeros[i + 1]
        assert len(numeros) == total


# ── Property 9 ────────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 9: última sessão concluída → ciclo concluido


@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(total=st.integers(min_value=1, max_value=10))
def test_property_9_ultima_sessao_conclui_ciclo(total):
    """Req 5.4, 6.4 — concluir última sessão marca ciclo.status='concluido'."""
    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        treino_obj = _criar_treino(session, usuario.id)
        ciclo_obj = _criar_ciclo(session, usuario.id)

        svc = CicloService(session)
        for n in range(1, total + 1):
            svc.adicionar_sessao(ciclo_obj.id, n, treino_obj.id)

        while True:
            proxima = svc.obter_proxima_sessao(usuario.id)
            if proxima is None:
                break
            svc.concluir_sessao(proxima["ciclo_sessao_id"])

        ciclo_final = CicloRepositorio(session).obter_ciclo_por_id(ciclo_obj.id)
        assert ciclo_final.status == "concluido"
        assert svc.obter_proxima_sessao(usuario.id) is None


# ── Property 10 ───────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 10: percentual_conclusao = round(concluidas/total*100, 1)


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(
    concluidas=st.integers(min_value=0, max_value=100),
    total=st.integers(min_value=1, max_value=100),
)
def test_property_10_percentual_progresso(concluidas, total):
    """Req 7.1, 7.3 — percentual_conclusao == round(concluidas/total*100, 1)."""
    assume(concluidas <= total)

    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        treino_obj = _criar_treino(session, usuario.id)
        ciclo_obj = _criar_ciclo(session, usuario.id)

        svc = CicloService(session)
        sessoes = [svc.adicionar_sessao(ciclo_obj.id, n, treino_obj.id) for n in range(1, total + 1)]
        for i in range(concluidas):
            svc.concluir_sessao(sessoes[i].id)

        progresso = svc.obter_progresso_ciclo(ciclo_obj.id)
        esperado = round((concluidas / total) * 100, 1)

        assert progresso["percentual_conclusao"] == esperado
        assert progresso["sessoes_concluidas"] == concluidas
        assert progresso["total_sessoes"] == total


# ── Property 11 ───────────────────────────────────────────────────────────────
# Feature: training-cycles, Property 11: listar_ciclos_por_usuario ordenado por data_inicio DESC


@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(datas=st.lists(
    st.dates(min_value=date(2020, 1, 1), max_value=date(2040, 12, 31)),
    min_size=2,
    max_size=5,
    unique=True,
))
def test_property_11_listagem_ordenada_por_data(datas):
    """Req 8.1 — ciclos listados por data_inicio decrescente."""
    with _fresh_db() as session:
        usuario = _criar_usuario(session)
        svc = CicloService(session)
        repo = CicloRepositorio(session)

        for i, d in enumerate(datas):
            ciclo_obj = svc.criar_ciclo(usuario.id, f"Ciclo {i}", d)
            c = repo.obter_ciclo_por_id(ciclo_obj.id)
            c.status = "concluido"
            repo.atualizar_ciclo(c)

        ciclos = svc.listar_ciclos_por_usuario(usuario.id)
        datas_retornadas = [c.data_inicio for c in ciclos]
        assert datas_retornadas == sorted(datas_retornadas, reverse=True)
