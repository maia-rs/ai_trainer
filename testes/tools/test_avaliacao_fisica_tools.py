from app.tools.avaliacao_fisica import atualizar_avaliacao_fisica as atualizar_module
from app.tools.avaliacao_fisica import obter_avaliacao_fisica as obter_module
from app.tools.avaliacao_fisica import obter_historico_avaliacao_fisica as historico_module
from app.tools.avaliacao_fisica import registrar_avaliacao_fisica as registrar_module


class DummySession:
    def close(self):
        return None


class DummyObj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def model_dump(self):
        return dict(self.__dict__)


def test_obter_avaliacao_fisica_ultima_sucesso(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def obter_ultima_avaliacao_por_usuario(self, usuario_id):
            return DummyObj(id="a1", usuario_id=usuario_id)

    monkeypatch.setattr(obter_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(obter_module, "AvaliacaoService", Service)

    resultado = obter_module.obter_avaliacao_fisica.invoke({"usuario_id": "u1"})
    assert resultado["item"]["id"] == "a1"


def test_obter_historico_avaliacao_fisica_erro(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def listar_avaliacoes_por_usuario(self, usuario_id):
            raise ValueError("usuario invalido")

    monkeypatch.setattr(historico_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(historico_module, "AvaliacaoService", Service)

    resultado = historico_module.obter_historico_avaliacao_fisica.invoke({"usuario_id": "u1"})
    assert resultado == {"error": "usuario invalido"}


def test_registrar_avaliacao_fisica_sucesso(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def criar_avaliacao(self, payload):
            return DummyObj(id="a1", usuario_id=payload.usuario_id)

    monkeypatch.setattr(registrar_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(registrar_module, "AvaliacaoService", Service)

    resultado = registrar_module.registrar_avaliacao_fisica.invoke(
        {
            "usuario_id": "u1",
            "peso": 80,
            "altura": 180,
            "percentual_gordura": 18,
            "massa_gorda": 14,
            "massa_muscular": 35,
            "imc": 24,
            "gordura_visceral": 8,
            "agua_corporal": 40,
            "taxa_metabolica_basal": 1700,
        }
    )

    assert resultado["id"] == "a1"


def test_atualizar_avaliacao_fisica_nao_encontrada(monkeypatch):
    class Service:
        def __init__(self, session):
            pass

        def atualizar_avaliacao(self, avaliacao_id, payload):
            return None

    monkeypatch.setattr(atualizar_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(atualizar_module, "AvaliacaoService", Service)

    resultado = atualizar_module.atualizar_avaliacao_fisica.invoke({"avaliacao_id": "x"})
    assert resultado == {"message": "Avaliacao nao encontrada."}
