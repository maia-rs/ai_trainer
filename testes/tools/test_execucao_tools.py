from datetime import datetime, timezone

from app.tools.execucao import obter_historico_treino as historico_module
from app.tools.execucao import obter_ultima_execucao as ultima_module
from app.tools.execucao import registrar_execucao_treino as registrar_module


class DummySession:
    def close(self):
        return None


class DummyExecucao:
    def __init__(self, treino_exercicio_id, data_execucao, carga=10, repeticoes=8, series=3):
        self.treino_exercicio_id = treino_exercicio_id
        self.data_execucao = data_execucao
        self.carga = carga
        self.repeticoes = repeticoes
        self.series = series

    def model_dump(self):
        return {
            "treino_exercicio_id": self.treino_exercicio_id,
            "data_execucao": self.data_execucao,
            "carga": self.carga,
            "repeticoes": self.repeticoes,
            "series": self.series,
        }


class DummyRelacao:
    def __init__(self, exercicio_id):
        self.exercicio_id = exercicio_id


def test_registrar_execucao_treino_sucesso(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def registrar_execucao(self, payload):
            return DummyExecucao(payload.treino_exercicio_id, payload.data_execucao)

    monkeypatch.setattr(registrar_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(registrar_module, "ExecucaoService", Service)

    resultado = registrar_module.registrar_execucao_treino.invoke(
        {
            "usuario_id": "u1",
            "treino_exercicio_id": "te1",
            "carga": 20,
            "repeticoes": 10,
            "series": 4,
            "duracao": 300,
        }
    )

    assert resultado["treino_exercicio_id"] == "te1"


def test_registrar_execucao_treino_data_invalida(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

    monkeypatch.setattr(registrar_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(registrar_module, "ExecucaoService", Service)

    resultado = registrar_module.registrar_execucao_treino.invoke(
        {
            "usuario_id": "u1",
            "treino_exercicio_id": "te1",
            "carga": 20,
            "repeticoes": 10,
            "series": 4,
            "duracao": 300,
            "data_execucao_iso": "invalida",
        }
    )

    assert "error" in resultado


def test_obter_historico_treino_filtra_por_exercicio(monkeypatch):
    class ExecService:
        def __init__(self, session):
            pass

        def listar_execucoes_por_usuario(self, usuario_id):
            agora = datetime.now(timezone.utc)
            return [DummyExecucao("te1", agora), DummyExecucao("te2", agora)]

    class RelService:
        def __init__(self, session):
            pass

        def obter_treino_exercicio_por_id(self, treino_exercicio_id):
            return DummyRelacao("e1" if treino_exercicio_id == "te1" else "e2")

    monkeypatch.setattr(historico_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(historico_module, "ExecucaoService", ExecService)
    monkeypatch.setattr(historico_module, "TreinoExercicioService", RelService)

    resultado = historico_module.obter_historico_treino.invoke(
        {"usuario_id": "u1", "exercicio_id": "e1"}
    )

    assert resultado["count"] == 1


def test_obter_ultima_execucao_sem_execucao(monkeypatch):
    class ExecService:
        def __init__(self, session):
            pass

        def listar_execucoes_por_usuario(self, usuario_id):
            return []

    class RelService:
        def __init__(self, session):
            pass

    monkeypatch.setattr(ultima_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(ultima_module, "ExecucaoService", ExecService)
    monkeypatch.setattr(ultima_module, "TreinoExercicioService", RelService)

    resultado = ultima_module.obter_ultima_execucao.invoke({"usuario_id": "u1"})
    assert resultado == {"message": "Nenhuma execucao encontrada."}
