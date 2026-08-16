from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.service.progresso_service import ProgressoService


class _StubAvaliacaoRepo:
    def __init__(self, avaliacoes_periodo=None, por_id=None):
        self.avaliacoes_periodo = avaliacoes_periodo if avaliacoes_periodo is not None else []
        self.por_id = por_id if por_id is not None else {}

    def obter_avaliacoes_por_periodo(self, _inicio, _fim):
        return self.avaliacoes_periodo

    def obter_avaliacao_por_id(self, avaliacao_id):
        return self.por_id.get(avaliacao_id)


class _StubExecucaoRepo:
    def __init__(self, periodo=None, por_exercicio_periodo=None):
        self.periodo = periodo if periodo is not None else []
        self.por_exercicio_periodo = por_exercicio_periodo if por_exercicio_periodo is not None else []

    def obter_execucoes_por_periodo(self, _inicio, _fim):
        return self.periodo

    def obter_execucoes_por_exercicio_e_periodo(self, _exercicio_id, _inicio, _fim):
        return self.por_exercicio_periodo


class _StubTreinoExercicioRepo:
    def __init__(self, relacoes=None):
        self.relacoes = relacoes if relacoes is not None else []

    def obter_treinos_exercicios_por_treino_id(self, _treino_id):
        return self.relacoes


class _StubExercicioRepo:
    def __init__(self, exercicios=None):
        self.exercicios = exercicios if exercicios is not None else {}

    def obter_exercicio_por_id(self, exercicio_id):
        return self.exercicios.get(exercicio_id)


def _build_service(db_session):
    return ProgressoService(db_session)


def test_obter_peso_evolucao_ordena_por_data(db_session):
    service = _build_service(db_session)
    aval1 = SimpleNamespace(data_avaliacao=datetime.now(timezone.utc) - timedelta(days=1), peso=79)
    aval2 = SimpleNamespace(data_avaliacao=datetime.now(timezone.utc) - timedelta(days=3), peso=81)
    service.avaliacao_fisica_repositorio = _StubAvaliacaoRepo(avaliacoes_periodo=[aval1, aval2])

    resultado = service.obter_peso_evolucao(datetime.now(timezone.utc) - timedelta(days=10), datetime.now(timezone.utc))

    assert resultado[0].peso == 81
    assert resultado[1].peso == 79


def test_obter_peso_evolucao_data_invalida(db_session):
    service = _build_service(db_session)

    with pytest.raises(ValueError, match="data de início"):
        service.obter_peso_evolucao(datetime.now(timezone.utc), datetime.now(timezone.utc) - timedelta(days=1))


def test_obter_volume_treino_calcula_total(db_session):
    service = _build_service(db_session)
    exec1 = SimpleNamespace(carga=50, repeticoes_realizadas=10)
    exec2 = SimpleNamespace(carga=60, repeticoes_realizadas=8)
    service.execucao_repositorio = _StubExecucaoRepo(periodo=[exec1, exec2])

    volume = service.obter_volume_treino(datetime.now(timezone.utc) - timedelta(days=7), datetime.now(timezone.utc))

    assert volume == 980


def test_comparar_avaliacoes_fisicas(db_session):
    service = _build_service(db_session)
    a1 = SimpleNamespace(peso=82, percentual_gordura=18, massa_muscular=36, data_avaliacao=datetime.now(timezone.utc) - timedelta(days=30))
    a2 = SimpleNamespace(peso=80, percentual_gordura=16, massa_muscular=37, data_avaliacao=datetime.now(timezone.utc) - timedelta(days=1))
    service.avaliacao_fisica_repositorio = _StubAvaliacaoRepo(por_id={"a1": a1, "a2": a2})

    comparacao = service.comparar_avaliacoes_fisicas("a1", "a2")

    assert comparacao["peso"] == (82, 80)
    assert comparacao["percentual_gordura"] == (18, 16)


def test_obter_evolucao_treino_dia_monta_estrutura(db_session):
    service = _build_service(db_session)
    relacao = SimpleNamespace(id="te-1", exercicio_id="ex-1", series=4, repeticoes=10, tempo_descanso=90)
    exercicio = SimpleNamespace(id="ex-1", nome="Supino")
    execucao = SimpleNamespace(treino_exercicio_id="te-1", data_execucao=datetime.now(timezone.utc), carga=60)

    service.treino_exercicio_repositorio = _StubTreinoExercicioRepo(relacoes=[relacao])
    service.exercicio_repositorio = _StubExercicioRepo(exercicios={"ex-1": exercicio})
    service.execucao_repositorio = _StubExecucaoRepo(periodo=[execucao])

    evolucao = service.obter_evolucao_treino_dia("treino-1")

    assert len(evolucao) == 1
    assert evolucao[0]["treino_exercicio_id"] == "te-1"
    assert evolucao[0]["nome_exercicio"] == "Supino"
    assert len(evolucao[0]["historico"]) == 1


def test_obter_metricas_dashboard_sem_periodo(db_session):
    service = _build_service(db_session)

    metricas = service.obter_metricas_dashboard()

    assert metricas["peso_atual"] is None
    assert metricas["frequencia_treino"] == 0


def test_obter_metricas_dashboard_periodo_invalido(db_session):
    service = _build_service(db_session)
    inicio = datetime.now(timezone.utc)
    fim = inicio - timedelta(days=1)

    with pytest.raises(ValueError, match="data de início"):
        service.obter_metricas_dashboard(inicio, fim)
