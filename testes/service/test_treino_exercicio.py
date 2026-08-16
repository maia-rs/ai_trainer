import pytest

from app.schemas.exercicio import ExercicioCreate, ExercicioResponse
from app.schemas.treino import TreinoCreate, TreinoResponse
from app.schemas.treino_exercicio import TreinoExercicioCreate, TreinoExercicioResponse, TreinoExercicioUpdate
from app.schemas.usuario import UsuarioCreate
from app.service.exercicio_service import ExercicioService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService


def _criar_usuario_ativo(db_session, nome: str = "Usuario Teste", telefone: str = "11911112222"):
    usuario_service = UsuarioService(db_session)
    return usuario_service.criar_usuario(UsuarioCreate(name=nome, telefone=telefone))


def _criar_treino_para_usuario(db_session, usuario_id: str, dia_da_semana: str = "Segunda-feira"):
    treino_service = TreinoService(db_session)
    treino_create = TreinoCreate(
        usuario_id=usuario_id,
        nome="Treino Teste",
        descricao="Descricao do Treino Teste",
        dia_da_semana=dia_da_semana,
    )
    return treino_service.criar_treino(treino_create)


def _criar_exercicio(db_session, suffix: str = "1"):
    exercicio_service = ExercicioService(db_session)
    exercicio_create = ExercicioCreate(
        id_externo=f"ext-{suffix}",
        nome=f"Exercicio Teste {suffix}",
        categoria="Forca",
        rotulo="Supino",
        grupo_muscular="Peito",
        equipamento="Barra",
        instrucao="Executar com tecnica controlada.",
        gif_url="https://example.com/exercicio.gif",
    )
    return exercicio_service.criar_exercicio(exercicio_create)


def test_criar_treino_exercicio(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session)

    service = TreinoExercicioService(db_session)
    response = service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=3,
            repeticoes=12,
            descanso=60,
        )
    )

    assert isinstance(response, TreinoExercicioResponse)
    assert response.treino_id == treino.id
    assert response.exercicio_id == exercicio.id
    assert response.series == 3
    assert response.repeticoes == 12
    assert response.descanso == 60


def test_criar_treino_exercicio_usuario_inativo(db_session):
    usuario = _criar_usuario_ativo(db_session, nome="Usuario Inativo", telefone="11999998888")
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    UsuarioService(db_session).desativar_usuario(usuario.id)
    exercicio = _criar_exercicio(db_session)
    service = TreinoExercicioService(db_session)

    with pytest.raises(ValueError, match="Usuário não está ativo"):
        service.criar_treino_exercicio(
            TreinoExercicioCreate(
                treino_id=treino.id,
                exercicio_id=exercicio.id,
                series=3,
                repeticoes=12,
                descanso=60,
            )
        )


def test_criar_treino_exercicio_treino_inativo(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    TreinoService(db_session).desativar_treino(treino.id)

    exercicio = _criar_exercicio(db_session)
    service = TreinoExercicioService(db_session)

    with pytest.raises(ValueError, match="Treino não está ativo"):
        service.criar_treino_exercicio(
            TreinoExercicioCreate(
                treino_id=treino.id,
                exercicio_id=exercicio.id,
                series=3,
                repeticoes=12,
                descanso=60,
            )
        )


def test_obter_treino_exercicio_por_id(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session)

    service = TreinoExercicioService(db_session)
    criado = service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=5,
            repeticoes=8,
            descanso=120,
        )
    )

    obtido = service.obter_treino_exercicio_por_id(criado.id)
    assert isinstance(obtido, TreinoExercicioResponse)
    assert obtido.id == criado.id
    assert obtido.descanso == 120


def test_adicionar_exercicio(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session)

    service = TreinoExercicioService(db_session)
    response = service.adicionar_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=4,
            repeticoes=10,
            descanso=90,
        )
    )

    assert isinstance(response, TreinoExercicioResponse)
    assert response.series == 4
    assert response.descanso == 90


def test_obter_exercicio_por_id(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session)

    service = TreinoExercicioService(db_session)
    criado = service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=5,
            repeticoes=8,
            descanso=120,
        )
    )

    obtido = service.obter_exercicio_por_id(criado.id)
    assert isinstance(obtido, TreinoExercicioResponse)
    assert obtido.id == criado.id


def test_obter_treino_por_dia(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id, dia_da_semana="Quinta-feira")

    service = TreinoExercicioService(db_session)
    obtido = service.obter_treino_por_dia("Quinta-feira")

    assert isinstance(obtido, TreinoResponse)
    assert obtido.id == treino.id


def test_obter_treino_por_dia_inexistente(db_session):
    usuario = _criar_usuario_ativo(db_session)
    _criar_treino_para_usuario(db_session, usuario.id, dia_da_semana="Sexta-feira")

    service = TreinoExercicioService(db_session)
    assert service.obter_treino_por_dia("Domingo") is None


def test_listar_exercicios_por_treino(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio1 = _criar_exercicio(db_session, suffix="1")
    exercicio2 = _criar_exercicio(db_session, suffix="2")

    service = TreinoExercicioService(db_session)
    service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio1.id,
            series=3,
            repeticoes=12,
            descanso=60,
        )
    )
    service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio2.id,
            series=4,
            repeticoes=10,
            descanso=90,
        )
    )

    relacoes = service.listar_exercicios_por_treino(treino.id)
    assert len(relacoes) == 2
    assert all(isinstance(relacao, TreinoExercicioResponse) for relacao in relacoes)


def test_obter_exercicios_por_treino(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session)

    service = TreinoExercicioService(db_session)
    service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=3,
            repeticoes=12,
            descanso=60,
        )
    )

    exercicios = service.obter_exercicios_por_treino(treino.id)
    assert len(exercicios) == 1
    assert isinstance(exercicios[0], ExercicioResponse)
    assert exercicios[0].id == exercicio.id


def test_obter_exercicio_por_treino(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session)

    service = TreinoExercicioService(db_session)
    service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=3,
            repeticoes=12,
            descanso=60,
        )
    )

    relacao = service.obter_exercicio_por_treino(treino.id, exercicio.id)
    assert isinstance(relacao, TreinoExercicioResponse)
    assert relacao.treino_id == treino.id
    assert relacao.exercicio_id == exercicio.id


def test_atualizar_treino_exercicio(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session)

    service = TreinoExercicioService(db_session)
    criado = service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=3,
            repeticoes=12,
            descanso=60,
        )
    )

    atualizado = service.atualizar_treino_exercicio(
        criado.id,
        TreinoExercicioUpdate(series=4, repeticoes=10, descanso=90),
    )

    assert isinstance(atualizado, TreinoExercicioResponse)
    assert atualizado.series == 4
    assert atualizado.repeticoes == 10
    assert atualizado.descanso == 90


def test_atualizar_exercicio(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session)

    service = TreinoExercicioService(db_session)
    criado = service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=3,
            repeticoes=12,
            descanso=60,
        )
    )

    atualizado = service.atualizar_exercicio(
        criado.id,
        TreinoExercicioUpdate(series=5, repeticoes=15, descanso=120),
    )

    assert isinstance(atualizado, TreinoExercicioResponse)
    assert atualizado.series == 5
    assert atualizado.repeticoes == 15
    assert atualizado.descanso == 120


def test_deletar_treino_exercicio(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session)

    service = TreinoExercicioService(db_session)
    criado = service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=3,
            repeticoes=12,
            descanso=60,
        )
    )

    assert service.deletar_treino_exercicio(criado.id) is True
    assert service.obter_treino_exercicio_por_id(criado.id) is None


def test_remover_exercicio(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino = _criar_treino_para_usuario(db_session, usuario.id)
    exercicio = _criar_exercicio(db_session)

    service = TreinoExercicioService(db_session)
    criado = service.criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino.id,
            exercicio_id=exercicio.id,
            series=3,
            repeticoes=12,
            descanso=60,
        )
    )

    assert service.remover_exercicio(criado.id) is True
    assert service.obter_treino_exercicio_por_id(criado.id) is None
