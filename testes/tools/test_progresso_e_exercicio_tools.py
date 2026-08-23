from datetime import datetime, timezone

from app.tools.exercicio import buscar_informacoes_exercicio as buscar_exercicio_module
from app.tools.progresso import comparar_avaliacoes_fisicas as comparar_module
from app.tools.progresso import obter_progresso as obter_progresso_module
from app.tools.progresso import obter_progresso_exercicio as progresso_exercicio_module
from app.tools.progresso import obter_resumo_progresso as resumo_module


class DummySession:
    def close(self):
        return None


class DummyObj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def model_dump(self):
        return dict(self.__dict__)


class DummyExecucao:
    def __init__(self, treino_exercicio_id="te1", carga=20, repeticoes=10, series=3):
        self.treino_exercicio_id = treino_exercicio_id
        self.data_execucao = datetime.now(timezone.utc)
        self.carga = carga
        self.repeticoes = repeticoes
        self.series = series

    def model_dump(self):
        return {
            "treino_exercicio_id": self.treino_exercicio_id,
            "carga": self.carga,
            "repeticoes": self.repeticoes,
            "series": self.series,
            "data_execucao": self.data_execucao,
        }


def test_buscar_informacoes_exercicio_sucesso(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def search_exercicios(self, nome=None, categoria=None, grupo_muscular=None, limite=5):
            if nome == "supino":
                return [
                    DummyObj(
                        id="e1",
                        id_externo="ext1",
                        nome="Supino",
                        categoria="Peito",
                        grupo_muscular="Peitoral",
                        equipamento="Barra",
                        instrucao="Executar",
                        gif_url="http://gif",
                    )
                ]
            return []

    monkeypatch.setattr(buscar_exercicio_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(buscar_exercicio_module, "ExercicioService", Service)

    resultado = buscar_exercicio_module.buscar_informacoes_exercicio.invoke(
        {"consultas": ["supino"], "limite": 3}
    )

    assert resultado["count"] == 1
    assert resultado["items"][0]["nome"] == "Supino"


def test_buscar_informacoes_exercicio_sem_resultado(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def search_exercicios(self, nome=None, categoria=None, grupo_muscular=None, limite=5):
            return []

    monkeypatch.setattr(buscar_exercicio_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(buscar_exercicio_module, "ExercicioService", Service)

    resultado = buscar_exercicio_module.buscar_informacoes_exercicio.invoke(
        {"consultas": ["xyz"]}
    )
    assert "message" in resultado


def test_buscar_informacoes_exercicio_reescreve_base_url_do_gif(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def search_exercicios(self, nome=None, categoria=None, grupo_muscular=None, limite=5):
            if nome == "sumo squat":
                return [
                    DummyObj(
                        id="e2",
                        id_externo="ext2",
                        nome="Smith Sumo Squat",
                        categoria="Pernas",
                        grupo_muscular="Quadríceps",
                        equipamento="Smith",
                        instrucao="Executar",
                        gif_url="https://orie.ia.br/exercises/videos/3142-dzz6BiV.gif",
                    )
                ]
            return []

    monkeypatch.setattr(buscar_exercicio_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(buscar_exercicio_module, "ExercicioService", Service)
    monkeypatch.setattr(
        buscar_exercicio_module.config,
        "BASE_URL",
        "https://aitrainer.orie.ia.br",
    )

    resultado = buscar_exercicio_module.buscar_informacoes_exercicio.invoke(
        {"consultas": ["sumo squat"], "limite": 1}
    )

    assert resultado["count"] == 1
    assert (
        resultado["items"][0]["gif_url"]
        == "https://aitrainer.orie.ia.br/exercises/videos/3142-dzz6BiV.gif"
    )


def test_obter_progresso_sucesso(monkeypatch):
    class ExecService:
        def __init__(self, session):
            pass

        def listar_execucoes_por_usuario(self, usuario_id):
            return [DummyExecucao()]

    class RelService:
        def __init__(self, session):
            pass

        def obter_treino_exercicio_por_id(self, treino_exercicio_id):
            return DummyObj(exercicio_id="e1")

    class AvalService:
        def __init__(self, session):
            pass

        def obter_ultima_avaliacao_por_usuario(self, usuario_id):
            return DummyObj(id="a1")

    monkeypatch.setattr(obter_progresso_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(obter_progresso_module, "ExecucaoService", ExecService)
    monkeypatch.setattr(obter_progresso_module, "TreinoExercicioService", RelService)
    monkeypatch.setattr(obter_progresso_module, "AvaliacaoService", AvalService)

    resultado = obter_progresso_module.obter_progresso.invoke({"usuario_id": "u1"})

    assert resultado["total_execucoes"] == 1
    assert resultado["volume_total"] == 600


def test_obter_resumo_progresso_erro(monkeypatch):
    class ProgressoService:
        def __init__(self, session):
            pass

        def obter_resumo_progresso(self, inicio, fim):
            raise ValueError("periodo invalido")

    monkeypatch.setattr(resumo_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(resumo_module, "ProgressoService", ProgressoService)

    resultado = resumo_module.obter_resumo_progresso.invoke({"usuario_id": "u1"})
    assert resultado == {"error": "periodo invalido"}


def test_obter_progresso_exercicio_sucesso(monkeypatch):
    class ProgressoService:
        def __init__(self, session):
            pass

        def obter_exercicio_evolucao(self, exercicio_id, inicio, fim):
            return [DummyObj(id="x1")]

    monkeypatch.setattr(progresso_exercicio_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(progresso_exercicio_module, "ProgressoService", ProgressoService)

    resultado = progresso_exercicio_module.obter_progresso_exercicio.invoke(
        {"exercicio_id": "e1"}
    )
    assert resultado["count"] == 1


def test_comparar_avaliacoes_fisicas_erro(monkeypatch):
    class ProgressoService:
        def __init__(self, session):
            pass

        def comparar_avaliacoes_fisicas(self, avaliacao_id_1, avaliacao_id_2):
            raise ValueError("avaliacao nao encontrada")

    monkeypatch.setattr(comparar_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(comparar_module, "ProgressoService", ProgressoService)

    resultado = comparar_module.comparar_avaliacoes_fisicas.invoke(
        {"avaliacao_id_1": "a1", "avaliacao_id_2": "a2"}
    )
    assert resultado == {"error": "avaliacao nao encontrada"}
