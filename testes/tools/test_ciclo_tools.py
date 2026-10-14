"""Testes unitários para as tools de ciclo.

Cobre requisitos: 9.2, 9.3, 9.4, 9.5, 9.7
"""
from datetime import date, datetime, timezone

from app.tools.ciclo import criar_ciclo as criar_ciclo_module
from app.tools.ciclo import adicionar_sessao_ciclo as adicionar_sessao_module
from app.tools.ciclo import obter_proxima_sessao as obter_proxima_module
from app.tools.ciclo import concluir_sessao as concluir_sessao_module
from app.tools.ciclo import obter_progresso_ciclo as obter_progresso_module
from app.tools.ciclo import listar_ciclos_usuario as listar_ciclos_module


# ── Helpers ────────────────────────────────────────────────────────────────────


class DummySession:
    def close(self):
        pass


class DummyCicloResponse:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def model_dump(self):
        return dict(self.__dict__)


class DummySessaoResponse:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def model_dump(self):
        return dict(self.__dict__)


# ── criar_ciclo tool ───────────────────────────────────────────────────────────


def test_criar_ciclo_tool_retorna_status_ativo(monkeypatch):
    """Req 9.2 — tool criar_ciclo cria e retorna ciclo com status=ativo."""

    class MockCicloService:
        def __init__(self, session):
            pass

        def criar_ciclo(self, usuario_id, nome, data_inicio):
            return DummyCicloResponse(
                id="ciclo-1",
                usuario_id=usuario_id,
                nome=nome,
                data_inicio=data_inicio,
                status="ativo",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    monkeypatch.setattr(criar_ciclo_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(criar_ciclo_module, "CicloService", MockCicloService)

    resultado = criar_ciclo_module.criar_ciclo.invoke({
        "usuario_id": "u1",
        "nome": "Ciclo Teste",
        "data_inicio": "2027-01-01",
    })

    assert resultado["status"] == "ativo"
    assert resultado["id"] == "ciclo-1"


def test_criar_ciclo_tool_retorna_erro_em_dados_invalidos(monkeypatch):
    """Req 9.2 — tool retorna {"error": ...} quando service lança ValueError."""

    class MockCicloService:
        def __init__(self, session):
            pass

        def criar_ciclo(self, usuario_id, nome, data_inicio):
            raise ValueError("Já existe um ciclo ativo para este usuário.")

    monkeypatch.setattr(criar_ciclo_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(criar_ciclo_module, "CicloService", MockCicloService)

    resultado = criar_ciclo_module.criar_ciclo.invoke({
        "usuario_id": "u1",
        "nome": "Ciclo X",
        "data_inicio": "2027-01-01",
    })

    assert "error" in resultado


def test_criar_ciclo_tool_data_invalida_retorna_erro(monkeypatch):
    """tool retorna {"error": ...} para data em formato inválido."""
    monkeypatch.setattr(criar_ciclo_module, "SessionLocal", lambda: DummySession())

    resultado = criar_ciclo_module.criar_ciclo.invoke({
        "usuario_id": "u1",
        "nome": "Ciclo X",
        "data_inicio": "data-invalida",
    })

    assert "error" in resultado


# ── adicionar_sessao_ciclo tool ────────────────────────────────────────────────


def test_adicionar_sessao_ciclo_tool_retorna_sessao(monkeypatch):
    """Req 9.3 — tool adicionar_sessao_ciclo cria e retorna CicloSessaoResponse."""

    class MockCicloService:
        def __init__(self, session):
            pass

        def adicionar_sessao(self, ciclo_id, numero_sessao, treino_id):
            return DummySessaoResponse(
                id="sessao-1",
                ciclo_id=ciclo_id,
                numero_sessao=numero_sessao,
                treino_id=treino_id,
                concluido=False,
                data_conclusao=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    monkeypatch.setattr(adicionar_sessao_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(adicionar_sessao_module, "CicloService", MockCicloService)

    resultado = adicionar_sessao_module.adicionar_sessao_ciclo.invoke({
        "ciclo_id": "ciclo-1",
        "numero_sessao": 1,
        "treino_id": "treino-1",
    })

    assert resultado["id"] == "sessao-1"
    assert resultado["concluido"] is False


def test_adicionar_sessao_ciclo_tool_retorna_erro(monkeypatch):
    """tool retorna {"error": ...} quando service lança ValueError."""

    class MockCicloService:
        def __init__(self, session):
            pass

        def adicionar_sessao(self, ciclo_id, numero_sessao, treino_id):
            raise ValueError("Ciclo não encontrado.")

    monkeypatch.setattr(adicionar_sessao_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(adicionar_sessao_module, "CicloService", MockCicloService)

    resultado = adicionar_sessao_module.adicionar_sessao_ciclo.invoke({
        "ciclo_id": "inexistente",
        "numero_sessao": 1,
        "treino_id": "treino-1",
    })

    assert "error" in resultado


# ── obter_proxima_sessao tool ──────────────────────────────────────────────────


def test_obter_proxima_sessao_tool_retorna_sessao_com_treino_nome(monkeypatch):
    """Req 9.4 — tool retorna próxima sessão com treino_nome."""

    class MockCicloService:
        def __init__(self, session):
            pass

        def obter_proxima_sessao(self, usuario_id):
            return {
                "ciclo_sessao_id": "sessao-1",
                "numero_sessao": 1,
                "treino_id": "treino-1",
                "treino_nome": "Treino Força",
                "treino_descricao": "Descrição do treino",
            }

    monkeypatch.setattr(obter_proxima_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(obter_proxima_module, "CicloService", MockCicloService)

    resultado = obter_proxima_module.obter_proxima_sessao.invoke({"usuario_id": "u1"})

    assert resultado["proxima_sessao"]["treino_nome"] == "Treino Força"
    assert resultado["proxima_sessao"]["numero_sessao"] == 1


def test_obter_proxima_sessao_tool_sem_ciclo_retorna_none(monkeypatch):
    """tool retorna proxima_sessao=None quando não há ciclo ativo."""

    class MockCicloService:
        def __init__(self, session):
            pass

        def obter_proxima_sessao(self, usuario_id):
            return None

    monkeypatch.setattr(obter_proxima_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(obter_proxima_module, "CicloService", MockCicloService)

    resultado = obter_proxima_module.obter_proxima_sessao.invoke({"usuario_id": "u1"})

    assert resultado["proxima_sessao"] is None


# ── concluir_sessao tool ───────────────────────────────────────────────────────


def test_concluir_sessao_tool_retorna_proxima_sessao(monkeypatch):
    """Req 9.5 — tool concluir_sessao retorna sessão concluída e próxima sessão."""

    sessao_concluida = DummySessaoResponse(
        id="sessao-1",
        ciclo_id="ciclo-1",
        numero_sessao=1,
        treino_id="treino-1",
        concluido=True,
        data_conclusao=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    class MockCicloService:
        def __init__(self, session):
            pass

        def concluir_sessao(self, ciclo_sessao_id):
            return sessao_concluida

        def obter_proxima_sessao(self, usuario_id):
            return {
                "ciclo_sessao_id": "sessao-2",
                "numero_sessao": 2,
                "treino_id": "treino-1",
                "treino_nome": "Treino B",
                "treino_descricao": "Desc B",
            }

    class MockCicloSessaoRepo:
        def __init__(self, session):
            pass

        def obter_sessao_por_id(self, sessao_id):
            class FakeSessao:
                ciclo_id = "ciclo-1"
            return FakeSessao()

    class MockCicloRepo:
        def __init__(self, session):
            pass

        def obter_ciclo_por_id(self, ciclo_id):
            class FakeCiclo:
                usuario_id = "u1"
            return FakeCiclo()

    monkeypatch.setattr(concluir_sessao_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(concluir_sessao_module, "CicloService", MockCicloService)
    monkeypatch.setattr(concluir_sessao_module, "CicloSessaoRepositorio", MockCicloSessaoRepo)
    monkeypatch.setattr(concluir_sessao_module, "CicloRepositorio", MockCicloRepo)

    resultado = concluir_sessao_module.concluir_sessao.invoke({"ciclo_sessao_id": "sessao-1"})

    assert resultado["sessao_concluida"]["concluido"] is True
    assert resultado["proxima_sessao"]["numero_sessao"] == 2


def test_concluir_sessao_tool_retorna_erro_em_sessao_invalida(monkeypatch):
    """tool retorna {"error": ...} quando sessão não existe."""

    class MockCicloService:
        def __init__(self, session):
            pass

        def concluir_sessao(self, ciclo_sessao_id):
            raise ValueError("Sessão não encontrada.")

    monkeypatch.setattr(concluir_sessao_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(concluir_sessao_module, "CicloService", MockCicloService)

    resultado = concluir_sessao_module.concluir_sessao.invoke({"ciclo_sessao_id": "inexistente"})

    assert "error" in resultado


# ── obter_progresso_ciclo tool ─────────────────────────────────────────────────


def test_obter_progresso_ciclo_tool_retorna_metricas(monkeypatch):
    """Req 9.7 — tool retorna sessoes_concluidas, total_sessoes e percentual_conclusao."""

    class MockCicloService:
        def __init__(self, session):
            pass

        def obter_progresso_ciclo(self, ciclo_id):
            return {
                "sessoes_concluidas": 3,
                "total_sessoes": 6,
                "percentual_conclusao": 50.0,
            }

    monkeypatch.setattr(obter_progresso_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(obter_progresso_module, "CicloService", MockCicloService)

    resultado = obter_progresso_module.obter_progresso_ciclo.invoke({"ciclo_id": "ciclo-1"})

    assert resultado["sessoes_concluidas"] == 3
    assert resultado["total_sessoes"] == 6
    assert resultado["percentual_conclusao"] == 50.0


def test_obter_progresso_ciclo_tool_retorna_erro(monkeypatch):
    """tool retorna {"error": ...} quando service lança ValueError."""

    class MockCicloService:
        def __init__(self, session):
            pass

        def obter_progresso_ciclo(self, ciclo_id):
            raise ValueError("Ciclo não encontrado.")

    monkeypatch.setattr(obter_progresso_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(obter_progresso_module, "CicloService", MockCicloService)

    resultado = obter_progresso_module.obter_progresso_ciclo.invoke({"ciclo_id": "inexistente"})

    assert "error" in resultado


# ── listar_ciclos_usuario tool ─────────────────────────────────────────────────


def test_listar_ciclos_usuario_tool_retorna_lista(monkeypatch):
    """tool listar_ciclos_usuario retorna lista de ciclos."""

    class MockCicloService:
        def __init__(self, session):
            pass

        def listar_ciclos_por_usuario(self, usuario_id):
            return [
                DummyCicloResponse(
                    id="ciclo-1",
                    usuario_id=usuario_id,
                    nome="Ciclo A",
                    data_inicio=date(2027, 1, 1),
                    status="concluido",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ),
                DummyCicloResponse(
                    id="ciclo-2",
                    usuario_id=usuario_id,
                    nome="Ciclo B",
                    data_inicio=date(2027, 3, 1),
                    status="ativo",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ),
            ]

    monkeypatch.setattr(listar_ciclos_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(listar_ciclos_module, "CicloService", MockCicloService)

    resultado = listar_ciclos_module.listar_ciclos_usuario.invoke({"usuario_id": "u1"})

    assert len(resultado["ciclos"]) == 2
    assert resultado["ciclos"][0]["id"] == "ciclo-1"
