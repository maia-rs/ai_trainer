from app.tools.treino_exercicio import adicionar_exercicio_treino as adicionar_module
from app.tools.treino_exercicio import atualizar_exercicio_treino as atualizar_module
from app.tools.treino_exercicio import obter_exercicios_treino as obter_module
from app.tools.treino_exercicio import remover_exercicio_treino as remover_module


class DummySession:
    def close(self):
        return None


class DummyObj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def model_dump(self):
        return dict(self.__dict__)


def test_adicionar_exercicio_treino_sucesso(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def criar_treino_exercicio(self, payload):
            return DummyObj(id="te1", treino_id=payload.treino_id, exercicio_id=payload.exercicio_id)

    monkeypatch.setattr(adicionar_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(adicionar_module, "TreinoExercicioService", Service)

    resultado = adicionar_module.adicionar_exercicio_treino.invoke(
        {
            "treino_id": "t1",
            "exercicio_id": "e1",
            "series": 3,
            "repeticoes": 10,
            "descanso": 60,
        }
    )

    assert resultado["id"] == "te1"


def test_atualizar_exercicio_treino_nao_encontrado(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def atualizar_treino_exercicio(self, treino_exercicio_id, payload):
            return None

    monkeypatch.setattr(atualizar_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(atualizar_module, "TreinoExercicioService", Service)

    # Passa campo válido para chegar até o service
    resultado = atualizar_module.atualizar_exercicio_treino.invoke(
        {"treino_exercicio_id": "x", "series": 4}
    )
    assert resultado == {"message": "Relacao treino-exercicio nao encontrada."}


def test_remover_exercicio_treino_sucesso(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def deletar_treino_exercicio(self, treino_exercicio_id):
            return True

    monkeypatch.setattr(remover_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(remover_module, "TreinoExercicioService", Service)

    resultado = remover_module.remover_exercicio_treino.invoke({"treino_exercicio_id": "te1"})
    assert resultado == {"success": True}


def test_obter_exercicios_treino_retorna_itens(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def listar_treinos_exercicios_por_treino(self, treino_id):
            return [
                DummyObj(
                    id="te1",
                    exercicio_id="e1",
                    series=4,
                    repeticoes=8,
                    descanso=90,
                    observacoes="ok",
                )
            ]

        def obter_exercicios_por_treino(self, treino_id):
            return [DummyObj(id="e1", nome="Agachamento")]

    monkeypatch.setattr(obter_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(obter_module, "TreinoExercicioService", Service)

    resultado = obter_module.obter_exercicios_treino.invoke({"treino_id": "t1"})

    assert resultado["count"] == 1
    assert resultado["items"][0]["nome_exercicio"] == "Agachamento"