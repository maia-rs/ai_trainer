from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.schemas.avaliacao_fisica import AvaliacaoFisicaCreate
from app.schemas.execucao import ExecucaoCreate
from app.schemas.exercicio import ExercicioCreate
from app.schemas.treino import TreinoCreate
from app.schemas.treino_exercicio import TreinoExercicioCreate
from app.schemas.usuario import UsuarioCreate
from app.service.avaliacao_service import AvaliacaoService
from app.service.execucao_service import ExecucaoService
from app.service.exercicio_service import ExercicioService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService


def _dia_hoje_pt() -> str:
    dias = [
        "Segunda-feira",
        "Terca-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sabado",
        "Domingo",
    ]
    return dias[datetime.now(timezone.utc).weekday()]


def _seed_cenario(db_session):
    usuario_service = UsuarioService(db_session)
    treino_service = TreinoService(db_session)
    exercicio_service = ExercicioService(db_session)
    treino_exercicio_service = TreinoExercicioService(db_session)
    execucao_service = ExecucaoService(db_session)
    avaliacao_service = AvaliacaoService(db_session)

    usuario = usuario_service.criar_usuario(UsuarioCreate(name="Maria", telefone="11999998888"))

    treino = treino_service.criar_treino(
        TreinoCreate(
            usuario_id=usuario.id,
            nome="Treino A",
            descricao="Treino principal",
            dia_da_semana=_dia_hoje_pt(),
        )
    )

    exercicio = exercicio_service.criar_exercicio(
        ExercicioCreate(
            id_externo="ex-001",
            nome="Supino Reto",
            categoria="Peito",
            rotulo="Supino",
            grupo_muscular="Peitoral",
            equipamento="Barra",
            instrucao="Mantenha os ombros estaveis e execute o movimento completo.",
            gif_url="https://example.com/supino.gif",
        )
    )

    relacao = treino_exercicio_service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=4,
            repeticoes=10,
            descanso=90,
            observacoes="Foco em tecnica",
        )
    )

    execucao_service.registrar_execucao(
        ExecucaoCreate(
            usuario_id=usuario.id,
            treino_exercicio_id=relacao.id,
            data_execucao=datetime.now(timezone.utc) - timedelta(days=1),
            carga=60,
            series=4,
            repeticoes=10,
            tempo_descanso_real=90,
            duracao_execucao=1200,
            calorias_queimadas=180,
            frequencia_cardiaca_media=125,
            observacoes="Boa sessao",
        )
    )

    avaliacao = avaliacao_service.criar_avaliacao(
        AvaliacaoFisicaCreate(
            usuario_id=usuario.id,
            data_avaliacao=datetime.now(timezone.utc) - timedelta(days=2),
            peso=78.0,
            altura=178.0,
            percentual_gordura=15.0,
            massa_gorda=11.7,
            massa_muscular=34.0,
            imc=24.6,
            gordura_visceral=7.0,
            agua_corporal=43.0,
            taxa_metabolica_basal=1700.0,
            observacoes="Evolucao positiva",
        )
    )

    return usuario, treino, avaliacao


def test_dashboard_endpoints(db_session):
    usuario, treino, avaliacao = _seed_cenario(db_session)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        base_params = {"usuario_id": usuario.id}

        resposta_dashboard = client.get("/dashboard", params=base_params)
        assert resposta_dashboard.status_code == 200
        assert "resumo" in resposta_dashboard.json()

        resposta_treinos = client.get("/dashboard/treinos", params=base_params)
        assert resposta_treinos.status_code == 200
        assert len(resposta_treinos.json()["treinos"]) == 1

        resposta_treino = client.get(f"/dashboard/treinos/{treino.id}", params=base_params)
        assert resposta_treino.status_code == 200
        assert len(resposta_treino.json()["exercicios"]) == 1

        resposta_treino_dia = client.get("/dashboard/treino-do-dia", params=base_params)
        assert resposta_treino_dia.status_code == 200
        assert "treino" in resposta_treino_dia.json()

        resposta_evolucao = client.get("/dashboard/evolucao", params=base_params)
        assert resposta_evolucao.status_code == 200
        assert "historico_por_exercicio" in resposta_evolucao.json()

        resposta_avaliacoes = client.get("/dashboard/avaliacoes", params=base_params)
        assert resposta_avaliacoes.status_code == 200
        assert len(resposta_avaliacoes.json()["avaliacoes"]) == 1

        resposta_avaliacao = client.get(
            f"/dashboard/avaliacoes/{avaliacao.id}",
            params=base_params,
        )
        assert resposta_avaliacao.status_code == 200
        assert resposta_avaliacao.json()["avaliacao"]["id"] == avaliacao.id
    finally:
        app.dependency_overrides.clear()