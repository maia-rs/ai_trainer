from app.tools.treino import atualizar_treino as atualizar_treino_module
from app.tools.treino import criar_treino as criar_treino_module
from app.tools.treino import desativar_treino as desativar_treino_module
from app.tools.treino import obter_treino_do_dia as obter_treino_do_dia_module


class DummySession:
    def close(self):
        return None


class DummyObj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def model_dump(self):
        return dict(self.__dict__)


def test_criar_treino_sucesso(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def criar_treino(self, payload):
            return DummyObj(id="treino-1", usuario_id=payload.usuario_id, nome=payload.nome)

    monkeypatch.setattr(criar_treino_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(criar_treino_module, "TreinoService", Service)

    resultado = criar_treino_module.criar_treino.invoke(
        {
            "usuario_id": "u1",
            "nome": "Treino A",
            "descricao": "Desc",
            "dia_da_semana": "Segunda-feira",
        }
    )

    assert resultado["id"] == "treino-1"
    assert resultado["nome"] == "Treino A"


def test_atualizar_treino_nao_encontrado(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def atualizar_treino(self, treino_id, payload):
            return None

    monkeypatch.setattr(atualizar_treino_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(atualizar_treino_module, "TreinoService", Service)

    # Passa um campo válido — sem campos a tool retorna erro de validação antes de chamar o service
    resultado = atualizar_treino_module.atualizar_treino.invoke(
        {"treino_id": "inexistente", "nome": "Novo Nome"}
    )
    assert resultado == {"message": "Treino nao encontrado."}


def test_desativar_treino_retorna_erro(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def desativar_treino(self, treino_id):
            raise ValueError("falha")

    monkeypatch.setattr(desativar_treino_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(desativar_treino_module, "TreinoService", Service)

    resultado = desativar_treino_module.desativar_treino.invoke({"treino_id": "t1"})
    assert resultado == {"error": "falha"}


def test_obter_treino_do_dia_sucesso(monkeypatch):
    class TreinoService:
        def __init__(self, session):
            pass

        def listar_treinos_por_usuario(self, usuario_id):
            return [
                DummyObj(
                    id="t1",
                    usuario_id=usuario_id,
                    nome="Treino A",
                    descricao="Desc",
                    dia_da_semana="Segunda-feira",
                    status="ativo",
                )
            ]

    class TreinoExService:
        def __init__(self, session):
            pass

        def listar_treinos_exercicios_por_treino(self, treino_id):
            return [
                DummyObj(
                    id="te1",
                    exercicio_id="e1",
                    series=3,
                    repeticoes=10,
                    descanso=60,
                    observacoes=None,
                )
            ]

        def obter_exercicios_por_treino(self, treino_id):
            return [DummyObj(id="e1", nome="Supino")]

    monkeypatch.setattr(obter_treino_do_dia_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(obter_treino_do_dia_module, "TreinoService", TreinoService)
    monkeypatch.setattr(
        obter_treino_do_dia_module,
        "TreinoExercicioService",
        TreinoExService,
    )

    resultado = obter_treino_do_dia_module.obter_treino_do_dia.invoke(
        {"usuario_id": "u1", "data_iso": "2026-08-17"}
    )

    assert resultado["treino"]["id"] == "t1"
    assert resultado["exercicios"][0]["nome_exercicio"] == "Supino"


def test_obter_treino_do_dia_data_invalida(monkeypatch):
    class TreinoService:
        def __init__(self, session):
            pass

        def listar_treinos_por_usuario(self, usuario_id):
            return []

    class TreinoExService:
        def __init__(self, session):
            pass

    monkeypatch.setattr(obter_treino_do_dia_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(obter_treino_do_dia_module, "TreinoService", TreinoService)
    monkeypatch.setattr(
        obter_treino_do_dia_module,
        "TreinoExercicioService",
        TreinoExService,
    )

    resultado = obter_treino_do_dia_module.obter_treino_do_dia.invoke(
        {"usuario_id": "u1", "data_iso": "invalida"}
    )

    assert "error" in resultado