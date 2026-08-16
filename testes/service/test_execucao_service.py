from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.execucao import ExecucaoCreate, ExecucaoUpdate, ExecucaoResponse
from app.schemas.exercicio import ExercicioCreate
from app.schemas.treino import TreinoCreate
from app.schemas.treino_exercicio import TreinoExercicioCreate
from app.schemas.usuario import UsuarioCreate
from app.service.execucao_service import ExecucaoService
from app.service.exercicio_service import ExercicioService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService


def _criar_usuario(db_session, nome: str, telefone: str):
    return UsuarioService(db_session).criar_usuario(
        UsuarioCreate(name=nome, telefone=telefone)
    )


def _criar_treino(db_session, usuario_id: str, nome: str = "Treino Execucao"):
    return TreinoService(db_session).criar_treino(
        TreinoCreate(
            usuario_id=usuario_id,
            nome=nome,
            descricao="Treino para testes de execucao",
            dia_da_semana="Segunda-feira",
        )
    )


def _criar_exercicio(db_session, sufixo: str = "1"):
    return ExercicioService(db_session).criar_exercicio(
        ExercicioCreate(
            id_externo=f"exec-{sufixo}",
            nome=f"Exercicio Exec {sufixo}",
            categoria="Forca",
            rotulo="Agachamento",
            grupo_muscular="Pernas",
            equipamento="Barra",
            instrucao="Executar com postura adequada.",
            gif_url="https://example.com/exercicio-execucao.gif",
        )
    )


def _criar_treino_exercicio(db_session, treino_id: str, exercicio_id: str):
    return TreinoExercicioService(db_session).criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino_id,
            exercicio_id=exercicio_id,
            series=4,
            repeticoes=10,
            descanso=90,
        )
    )


def _payload_execucao(usuario_id: str, treino_exercicio_id: str) -> ExecucaoCreate:
    return ExecucaoCreate(
        usuario_id=usuario_id,
        treino_exercicio_id=treino_exercicio_id,
        data_execucao=datetime.now(timezone.utc) - timedelta(minutes=30),
        carga=60,
        series=4,
        repeticoes=10,
        tempo_descanso_real=75,
        duracao_execucao=1800,
        calorias_queimadas=220,
        frequencia_cardiaca_media=130,
        observacoes="Treino concluido sem intercorrencias",
    )


def test_registrar_execucao_com_sucesso(db_session):
    usuario = _criar_usuario(db_session, "Usuario Exec", "11910000001")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "1")
    treino_exercicio = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    service = ExecucaoService(db_session)
    response = service.registrar_execucao(_payload_execucao(usuario.id, treino_exercicio.id))

    assert isinstance(response, ExecucaoResponse)
    assert response.usuario_id == usuario.id
    assert response.treino_exercicio_id == treino_exercicio.id
    assert response.carga == 60
    assert response.series == 4
    assert response.repeticoes == 10


def test_registrar_execucao_com_data_futura_falha(db_session):
    usuario = _criar_usuario(db_session, "Usuario Futuro", "11910000002")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "2")
    treino_exercicio = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    payload = _payload_execucao(usuario.id, treino_exercicio.id)
    payload.data_execucao = datetime.now(timezone.utc) + timedelta(minutes=5)

    with pytest.raises(ValueError, match="data da execução não pode ser futura"):
        ExecucaoService(db_session).registrar_execucao(payload)


def test_registrar_execucao_com_carga_negativa_falha(db_session):
    usuario = _criar_usuario(db_session, "Usuario Carga", "11910000003")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "3")
    treino_exercicio = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    payload = _payload_execucao(usuario.id, treino_exercicio.id)
    payload.carga = -1

    with pytest.raises(ValueError, match="carga deve ser maior ou igual a zero"):
        ExecucaoService(db_session).registrar_execucao(payload)


def test_registrar_execucao_com_usuario_de_outro_treino_falha(db_session):
    usuario_dono_treino = _criar_usuario(db_session, "Usuario Dono", "11910000004")
    usuario_errado = _criar_usuario(db_session, "Usuario Errado", "11910000005")
    treino = _criar_treino(db_session, usuario_dono_treino.id)
    exercicio = _criar_exercicio(db_session, "4")
    treino_exercicio = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    payload = _payload_execucao(usuario_errado.id, treino_exercicio.id)

    with pytest.raises(ValueError, match="Usuário não pertence ao treino informado"):
        ExecucaoService(db_session).registrar_execucao(payload)


def test_obter_e_listar_execucoes_por_usuario(db_session):
    usuario = _criar_usuario(db_session, "Usuario Lista", "11910000006")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "5")
    treino_exercicio = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    service = ExecucaoService(db_session)
    execucao = service.registrar_execucao(_payload_execucao(usuario.id, treino_exercicio.id))

    obtida = service.obter_execucao_por_id(execucao.id)
    lista_usuario = service.listar_execucoes_por_usuario(usuario.id)

    assert obtida is not None
    assert obtida.id == execucao.id
    assert len(lista_usuario) == 1
    assert lista_usuario[0].usuario_id == usuario.id


def test_obter_ultimas_execucoes(db_session):
    usuario = _criar_usuario(db_session, "Usuario Ultimas", "11910000007")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "6")
    treino_exercicio = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    service = ExecucaoService(db_session)
    service.registrar_execucao(_payload_execucao(usuario.id, treino_exercicio.id))

    payload2 = _payload_execucao(usuario.id, treino_exercicio.id)
    payload2.data_execucao = datetime.now(timezone.utc) - timedelta(minutes=10)
    service.registrar_execucao(payload2)

    ultimas = service.obter_ultimas_execucoes(limite=1)
    assert len(ultimas) == 1


def test_atualizar_execucao(db_session):
    usuario = _criar_usuario(db_session, "Usuario Atualiza", "11910000008")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "7")
    treino_exercicio = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    service = ExecucaoService(db_session)
    execucao = service.registrar_execucao(_payload_execucao(usuario.id, treino_exercicio.id))

    atualizada = service.atualizar_execucao(
        execucao.id,
        ExecucaoUpdate(
            carga=70,
            series=5,
            repeticoes=8,
            observacoes="Carga aumentada",
        ),
    )

    assert atualizada is not None
    assert atualizada.carga == 70
    assert atualizada.series == 5
    assert atualizada.repeticoes == 8
    assert atualizada.observacoes == "Carga aumentada"


def test_deletar_execucao(db_session):
    usuario = _criar_usuario(db_session, "Usuario Deleta", "11910000009")
    treino = _criar_treino(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session, "8")
    treino_exercicio = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

    service = ExecucaoService(db_session)
    execucao = service.registrar_execucao(_payload_execucao(usuario.id, treino_exercicio.id))

    assert service.deletar_execucao(execucao.id) is True
    assert service.obter_execucao_por_id(execucao.id) is None
