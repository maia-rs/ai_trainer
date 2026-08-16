from app.tools.usuario import consultar_usuario as consultar_usuario_module
from app.tools.usuario import usuario_criar as usuario_criar_module


def test_criar_usuario_tool(db_session, db_session_factory, monkeypatch):
    monkeypatch.setattr(usuario_criar_module, "SessionLocal", db_session_factory)

    resultado = usuario_criar_module.criar_usuario.invoke(
        {"nome": "Ana Tool", "telefone": "11999998888"}
    )

    assert resultado["id"]
    assert resultado["name"] == "Ana Tool"
    assert resultado["telefone"] == "(11) 99999-8888"
    assert resultado["status"] == "ativo"


def test_criar_usuario_tool_retorna_erro_para_telefone_duplicado(
    db_session, db_session_factory, monkeypatch
):
    monkeypatch.setattr(usuario_criar_module, "SessionLocal", db_session_factory)

    usuario_criar_module.criar_usuario.invoke(
        {"nome": "Ana Tool", "telefone": "11999998888"}
    )
    resultado = usuario_criar_module.criar_usuario.invoke(
        {"nome": "Bruno Tool", "telefone": "11999998888"}
    )

    assert resultado == {"error": "Telefone já cadastrado."}


def test_consultar_usuario_tool(db_session, db_session_factory, monkeypatch):
    monkeypatch.setattr(usuario_criar_module, "SessionLocal", db_session_factory)
    monkeypatch.setattr(consultar_usuario_module, "SessionLocal", db_session_factory)

    criado = usuario_criar_module.criar_usuario.invoke(
        {"nome": "Bruno Tool", "telefone": "11999997777"}
    )
    resultado = consultar_usuario_module.consultar_usuario.invoke(
        {"telefone": "11999997777"}
    )

    assert resultado["id"] == criado["id"]
    assert resultado["name"] == "Bruno Tool"
    assert resultado["telefone"] == "(11) 99999-7777"
    assert resultado["status"] == "ativo"


def test_consultar_usuario_tool_quando_usuario_nao_existe(
    db_session, db_session_factory, monkeypatch
):
    monkeypatch.setattr(consultar_usuario_module, "SessionLocal", db_session_factory)

    resultado = consultar_usuario_module.consultar_usuario.invoke(
        {"telefone": "11999990000"}
    )

    assert resultado == {
        "message": "Usuário não encontrado. Deseja criar um novo usuário?"
    }


def test_criar_usuario_tool_com_telefone_invalido(
    db_session, db_session_factory, monkeypatch
):
    monkeypatch.setattr(usuario_criar_module, "SessionLocal", db_session_factory)

    resultado = usuario_criar_module.criar_usuario.invoke(
        {"nome": "Ana Tool", "telefone": "123"}
    )

    assert "Telefone inválido" in resultado["error"]


def test_consultar_usuario_tool_com_telefone_invalido(
    db_session, db_session_factory, monkeypatch
):
    monkeypatch.setattr(consultar_usuario_module, "SessionLocal", db_session_factory)

    resultado = consultar_usuario_module.consultar_usuario.invoke({"telefone": "123"})

    assert "Telefone inválido" in resultado["error"]