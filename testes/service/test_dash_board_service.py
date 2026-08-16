from types import SimpleNamespace

from app.service.dash_board_service import DashBoardService


class _StubTreinoExercicioService:
    def __init__(self, treino_do_dia=None):
        self.treino_do_dia = treino_do_dia

    def obter_treino_por_dia(self, _dia):
        return self.treino_do_dia


class _StubExercicioService:
    def __init__(self, exercicios=None):
        self.exercicios = exercicios if exercicios is not None else []

    def obter_exercicios_por_treino(self, _treino_id):
        return self.exercicios


class _StubExecucaoService:
    def __init__(self, execucoes=None):
        self.execucoes = execucoes if execucoes is not None else []

    def obter_ultimas_execucoes(self):
        return self.execucoes


class _StubProgressoService:
    def __init__(self, metricas=None, evolucao=None):
        self.metricas = metricas if metricas is not None else {}
        self.evolucao = evolucao if evolucao is not None else []

    def obter_metricas_dashboard(self):
        return self.metricas

    def obter_evolucao_treino_dia(self, _treino_id):
        return self.evolucao


def _build_service(db_session):
    return DashBoardService(db_session)


def test_obter_treino_do_dia_retorna_treino(db_session):
    service = _build_service(db_session)
    treino = SimpleNamespace(id="treino-1")
    service.treino_exercicio_service = _StubTreinoExercicioService(treino_do_dia=treino)

    resultado = service.obter_treino_do_dia()

    assert resultado.id == "treino-1"


def test_obter_resumo_progresso_geral_retorna_metricas(db_session):
    service = _build_service(db_session)
    metricas = {"volume_treino": 1200, "frequencia_treino": 3}
    service.progresso_service = _StubProgressoService(metricas=metricas)

    resultado = service.obter_resumo_progresso_geral()

    assert resultado == metricas


def test_obter_metricas_fisicas_retorna_metricas(db_session):
    service = _build_service(db_session)
    metricas = {"peso_atual": 80.0}
    service.progresso_service = _StubProgressoService(metricas=metricas)

    resultado = service.obter_metricas_fisicas()

    assert resultado == metricas


def test_obter_evolucao_treino_dia_sem_treino(db_session):
    service = _build_service(db_session)
    service.treino_exercicio_service = _StubTreinoExercicioService(treino_do_dia=None)

    resultado = service.obter_evolucao_treino_dia()

    assert resultado == {"mensagem": "Nenhum treino programado para hoje."}


def test_obter_evolucao_treino_dia_sem_exercicios(db_session):
    service = _build_service(db_session)
    treino = SimpleNamespace(id="treino-2")
    service.treino_exercicio_service = _StubTreinoExercicioService(treino_do_dia=treino)
    service.exercicio_service = _StubExercicioService(exercicios=[])

    resultado = service.obter_evolucao_treino_dia()

    assert resultado == {"mensagem": "Nenhum exercício encontrado para o treino do dia."}


def test_obter_evolucao_treino_dia_com_sucesso(db_session):
    service = _build_service(db_session)
    treino = SimpleNamespace(id="treino-3")
    evolucao = [{"treino_exercicio_id": "te-1", "historico": []}]

    service.treino_exercicio_service = _StubTreinoExercicioService(treino_do_dia=treino)
    service.exercicio_service = _StubExercicioService(exercicios=[SimpleNamespace(id="ex-1")])
    service.progresso_service = _StubProgressoService(evolucao=evolucao)

    resultado = service.obter_evolucao_treino_dia()

    assert resultado == evolucao


def test_obter_atividades_recentes(db_session):
    service = _build_service(db_session)
    atividades = [SimpleNamespace(id="exec-1"), SimpleNamespace(id="exec-2")]
    service.execucao_service = _StubExecucaoService(execucoes=atividades)

    resultado = service.obter_atividades_recentes()

    assert len(resultado) == 2
    assert resultado[0].id == "exec-1"
