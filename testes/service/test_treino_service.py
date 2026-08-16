from app.schemas.treino import TreinoCreate, TreinoUpdate, TreinoResponse
from app.schemas.usuario import UsuarioCreate
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService


def _criar_usuario_ativo(db_session):
    usuario_service = UsuarioService(db_session)
    return usuario_service.criar_usuario(
        UsuarioCreate(name="Usuario Teste", telefone="11911112222")
    )


def test_criar_treino(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino_service = TreinoService(db_session)

    treino_create = TreinoCreate(
        usuario_id=usuario.id,
        nome="Treino A",
        descricao="Descricao do Treino A",
        dia_da_semana="Segunda-feira",
    )

    treino_response = treino_service.criar_treino(treino_create)

    assert isinstance(treino_response, TreinoResponse)
    assert treino_response.nome == "Treino A"
    assert treino_response.descricao == "Descricao do Treino A"
    assert treino_response.dia_da_semana == "Segunda-feira"
    assert treino_response.usuario_id == usuario.id


def test_obter_treino_por_id(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino_service = TreinoService(db_session)

    treino_create = TreinoCreate(
        usuario_id=usuario.id,
        nome="Treino B",
        descricao="Descricao do Treino B",
        dia_da_semana="Terca-feira",
    )
    treino_response = treino_service.criar_treino(treino_create)

    treino_obtido = treino_service.obter_treino_por_id(treino_response.id)

    assert isinstance(treino_obtido, TreinoResponse)
    assert treino_obtido.id == treino_response.id
    assert treino_obtido.nome == "Treino B"
    assert treino_obtido.descricao == "Descricao do Treino B"
    assert treino_obtido.dia_da_semana == "Terca-feira"


def test_listar_treinos_por_usuario(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino_service = TreinoService(db_session)

    treino_service.criar_treino(
        TreinoCreate(
            usuario_id=usuario.id,
            nome="Treino C",
            descricao="Descricao do Treino C",
            dia_da_semana="Quarta-feira",
        )
    )

    treino_service.criar_treino(
        TreinoCreate(
            usuario_id=usuario.id,
            nome="Treino D",
            descricao="Descricao do Treino D",
            dia_da_semana="Quinta-feira",
        )
    )

    treinos_listados = treino_service.listar_treinos_por_usuario(usuario.id)

    assert isinstance(treinos_listados, list)
    assert len(treinos_listados) == 2
    for treino in treinos_listados:
        assert isinstance(treino, TreinoResponse)
        assert treino.usuario_id == usuario.id


def test_atualizar_treino(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino_service = TreinoService(db_session)

    treino_create = TreinoCreate(
        usuario_id=usuario.id,
        nome="Treino E",
        descricao="Descricao do Treino E",
        dia_da_semana="Sexta-feira",
    )
    treino_response = treino_service.criar_treino(treino_create)

    treino_update = TreinoUpdate(
        nome="Treino E Atualizado",
        descricao="Descricao atualizada do Treino E",
    )

    treino_atualizado = treino_service.atualizar_treino(treino_response.id, treino_update)

    assert isinstance(treino_atualizado, TreinoResponse)
    assert treino_atualizado.nome == "Treino E Atualizado"
    assert treino_atualizado.descricao == "Descricao atualizada do Treino E"


def test_duplicar_treino(db_session):
    usuario = _criar_usuario_ativo(db_session)
    treino_service = TreinoService(db_session)

    treino_create = TreinoCreate(
        usuario_id=usuario.id,
        nome="Treino G",
        descricao="Descricao do Treino G",
        dia_da_semana="Domingo",
    )
    treino_response = treino_service.criar_treino(treino_create)

    treino_duplicado = treino_service.duplicar_treino(treino_response.id)

    assert isinstance(treino_duplicado, TreinoResponse)
    assert treino_duplicado.nome == "Treino G (Copia)" or treino_duplicado.nome == "Treino G (Cópia)"
    assert treino_duplicado.descricao == "Descricao do Treino G"
    assert treino_duplicado.dia_da_semana == "Domingo"
    assert treino_duplicado.usuario_id == usuario.id
