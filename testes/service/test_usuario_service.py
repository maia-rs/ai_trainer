import pytest

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.service.usuario_service import UsuarioService


def test_criar_usuario_com_sucesso(db_session):
    service = UsuarioService(db_session)

    payload = UsuarioCreate(name="Ana", telefone="11999998888")
    usuario = service.criar_usuario(payload)

    assert usuario.id is not None
    assert usuario.name == "Ana"
    assert str(usuario.telefone) == "(11) 99999-8888"
    assert usuario.status == "ativo"


def test_nao_permite_telefone_duplicado(db_session):
    service = UsuarioService(db_session)

    service.criar_usuario(UsuarioCreate(name="Ana", telefone="11999998888"))

    with pytest.raises(ValueError, match="Telefone já cadastrado"):
        service.criar_usuario(UsuarioCreate(name="Bruno", telefone="11999998888"))

def test_obter_usuario_por_id(db_session):
    service = UsuarioService(db_session)

    usuario_criado = service.criar_usuario(UsuarioCreate(name="Carlos", telefone="11999997777"))
    usuario_obtido = service.obter_usuario_por_id(usuario_criado.id)

    assert usuario_obtido is not None
    assert usuario_obtido.id == usuario_criado.id
    assert usuario_obtido.name == "Carlos"
    assert str(usuario_obtido.telefone) == "(11) 99999-7777"

def test_obter_usuario_por_telefone(db_session):
    service = UsuarioService(db_session)

    usuario_criado = service.criar_usuario(UsuarioCreate(name="Diana", telefone="11999996666"))
    usuario_obtido = service.obter_usuario_por_telefone("11999996666")

    assert usuario_obtido is not None
    assert usuario_obtido.id == usuario_criado.id
    assert usuario_obtido.name == "Diana"
    assert str(usuario_obtido.telefone) == "(11) 99999-6666"

def test_atualizar_usuario(db_session):
    service = UsuarioService(db_session)

    usuario_criado = service.criar_usuario(UsuarioCreate(name="Eduardo", telefone="11999995555"))
    usuario_atualizado = service.atualizar_usuario(usuario_criado.id, UsuarioUpdate(name="Eduardo Silva", telefone="11999995555"))

    assert usuario_atualizado is not None
    assert usuario_atualizado.id == usuario_criado.id
    assert usuario_atualizado.name == "Eduardo Silva"
    assert str(usuario_atualizado.telefone) == "(11) 99999-5555"