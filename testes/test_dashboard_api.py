from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.dashboard_token import DashboardToken
from app.schemas.avaliacao_fisica import AvaliacaoFisicaCreate
from app.schemas.execucao import ExecucaoCreate
from app.schemas.exercicio import ExercicioCreate
from app.schemas.treino import TreinoCreate
from app.schemas.treino_exercicio import TreinoExercicioCreate
from app.schemas.usuario import UsuarioCreate
from app.service.avaliacao_service import AvaliacaoService
from app.service.dashboard_token_service import DashboardTokenService
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


# ---------------------------------------------------------------------------
# Testes do DashboardTokenService
# ---------------------------------------------------------------------------

class TestDashboardTokenService:

    def test_emitir_cria_token_valido(self, db_session):
        usuario = UsuarioService(db_session).criar_usuario(
            UsuarioCreate(name="Joao", telefone="11900000001")
        )
        service = DashboardTokenService(db_session)
        token = service.emitir(usuario_id=usuario.id, ttl_minutos=60)

        assert token.token
        assert token.usuario_id == usuario.id
        assert token.used is False
        expires = token.expires_at if token.expires_at.tzinfo else token.expires_at.replace(tzinfo=timezone.utc)
        assert expires > datetime.now(timezone.utc)

    def test_validar_token_valido(self, db_session):
        usuario = UsuarioService(db_session).criar_usuario(
            UsuarioCreate(name="Ana", telefone="11900000002")
        )
        service = DashboardTokenService(db_session)
        emitido = service.emitir(usuario_id=usuario.id, ttl_minutos=60)

        validado = service.validar(emitido.token)
        assert validado.usuario_id == usuario.id

    def test_validar_token_inexistente(self, db_session):
        service = DashboardTokenService(db_session)
        with pytest.raises(ValueError, match="Token inválido"):
            service.validar("token-que-nao-existe")

    def test_validar_token_expirado(self, db_session):
        usuario = UsuarioService(db_session).criar_usuario(
            UsuarioCreate(name="Carlos", telefone="11900000003")
        )
        service = DashboardTokenService(db_session)
        token = service.emitir(usuario_id=usuario.id, ttl_minutos=60)

        # Força expiração
        token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db_session.commit()

        with pytest.raises(ValueError, match="Token expirado"):
            service.validar(token.token)

    def test_validar_token_ja_usado(self, db_session):
        usuario = UsuarioService(db_session).criar_usuario(
            UsuarioCreate(name="Bia", telefone="11900000004")
        )
        service = DashboardTokenService(db_session)
        token = service.emitir(usuario_id=usuario.id, ttl_minutos=60)

        token.used = True
        db_session.commit()

        with pytest.raises(ValueError, match="Token já utilizado"):
            service.validar(token.token)

    def test_ttl_minimo_de_1_minuto(self, db_session):
        usuario = UsuarioService(db_session).criar_usuario(
            UsuarioCreate(name="Leo", telefone="11900000005")
        )
        service = DashboardTokenService(db_session)
        token = service.emitir(usuario_id=usuario.id, ttl_minutos=0)

        assert token.expires_at is not None
        expires = token.expires_at if token.expires_at.tzinfo else token.expires_at.replace(tzinfo=timezone.utc)
        assert expires > datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Testes dos endpoints do dashboard (com token)
# ---------------------------------------------------------------------------

class TestDashboardEndpoints:

    def _client_com_token(self, db_session, usuario_id: str):
        """Retorna (client, token_str) com override de sessão."""
        token_registro = DashboardTokenService(db_session).emitir(usuario_id=usuario_id)

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        return TestClient(app), token_registro.token

    def test_dashboard_com_token_valido(self, db_session):
        usuario, treino, avaliacao = _seed_cenario(db_session)
        client, token = self._client_com_token(db_session, usuario.id)
        try:
            resp = client.get("/dashboard", params={"token": token})
            assert resp.status_code == 200
            assert "resumo" in resp.json()
        finally:
            app.dependency_overrides.clear()

    def test_dashboard_sem_token_retorna_422(self, db_session):
        def override_get_db():
            yield db_session
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        try:
            resp = client.get("/dashboard")
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_dashboard_token_invalido_retorna_401(self, db_session):
        def override_get_db():
            yield db_session
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        try:
            resp = client.get("/dashboard", params={"token": "token-falso"})
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_dashboard_token_expirado_retorna_401(self, db_session):
        usuario, _, _ = _seed_cenario(db_session)
        service = DashboardTokenService(db_session)
        token = service.emitir(usuario_id=usuario.id, ttl_minutos=60)
        token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db_session.commit()

        def override_get_db():
            yield db_session
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        try:
            resp = client.get("/dashboard", params={"token": token.token})
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_listagem_treinos(self, db_session):
        usuario, treino, _ = _seed_cenario(db_session)
        client, token = self._client_com_token(db_session, usuario.id)
        try:
            resp = client.get("/dashboard/treinos", params={"token": token})
            assert resp.status_code == 200
            assert len(resp.json()["treinos"]) == 1
        finally:
            app.dependency_overrides.clear()

    def test_detalhar_treino(self, db_session):
        usuario, treino, _ = _seed_cenario(db_session)
        client, token = self._client_com_token(db_session, usuario.id)
        try:
            resp = client.get(f"/dashboard/treinos/{treino.id}", params={"token": token})
            assert resp.status_code == 200
            assert len(resp.json()["exercicios"]) == 1
        finally:
            app.dependency_overrides.clear()

    def test_treino_do_dia(self, db_session):
        usuario, _, _ = _seed_cenario(db_session)
        client, token = self._client_com_token(db_session, usuario.id)
        try:
            resp = client.get("/dashboard/treino-do-dia", params={"token": token})
            assert resp.status_code == 200
            assert "treino" in resp.json()
        finally:
            app.dependency_overrides.clear()

    def test_evolucao(self, db_session):
        usuario, _, _ = _seed_cenario(db_session)
        client, token = self._client_com_token(db_session, usuario.id)
        try:
            resp = client.get("/dashboard/evolucao", params={"token": token})
            assert resp.status_code == 200
            assert "historico_por_exercicio" in resp.json()
        finally:
            app.dependency_overrides.clear()

    def test_listar_avaliacoes(self, db_session):
        usuario, _, _ = _seed_cenario(db_session)
        client, token = self._client_com_token(db_session, usuario.id)
        try:
            resp = client.get("/dashboard/avaliacoes", params={"token": token})
            assert resp.status_code == 200
            assert len(resp.json()["avaliacoes"]) == 1
        finally:
            app.dependency_overrides.clear()

    def test_detalhar_avaliacao(self, db_session):
        usuario, _, avaliacao = _seed_cenario(db_session)
        client, token = self._client_com_token(db_session, usuario.id)
        try:
            resp = client.get(
                f"/dashboard/avaliacoes/{avaliacao.id}",
                params={"token": token},
            )
            assert resp.status_code == 200
            assert resp.json()["avaliacao"]["id"] == avaliacao.id
        finally:
            app.dependency_overrides.clear()

    def test_token_nao_acessa_dados_de_outro_usuario(self, db_session):
        """Token do usuário A não pode acessar avaliação do usuário B."""
        usuario_a, _, _ = _seed_cenario(db_session)

        usuario_b = UsuarioService(db_session).criar_usuario(
            UsuarioCreate(name="Pedro", telefone="11977776666")
        )
        avaliacao_b = AvaliacaoService(db_session).criar_avaliacao(
            AvaliacaoFisicaCreate(
                usuario_id=usuario_b.id,
                data_avaliacao=datetime.now(timezone.utc),
                peso=90.0,
                altura=180.0,
                percentual_gordura=20.0,
                massa_gorda=18.0,
                massa_muscular=30.0,
                imc=27.8,
                gordura_visceral=10.0,
                agua_corporal=40.0,
                taxa_metabolica_basal=1800.0,
                observacoes="",
            )
        )

        # Token gerado para usuário A
        client, token_a = self._client_com_token(db_session, usuario_a.id)
        try:
            resp = client.get(
                f"/dashboard/avaliacoes/{avaliacao_b.id}",
                params={"token": token_a},
            )
            # Deve retornar 404 pois a avaliação não pertence ao usuário A
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()
