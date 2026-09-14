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


from app.tools.usuario import atualizar_usuario as atualizar_usuario_module


def test_atualizar_usuario_meta_semanal(db_session, db_session_factory, monkeypatch):
    monkeypatch.setattr(usuario_criar_module, "SessionLocal", db_session_factory)
    monkeypatch.setattr(atualizar_usuario_module, "SessionLocal", db_session_factory)

    criado = usuario_criar_module.criar_usuario.invoke(
        {"nome": "Carlos Tool", "telefone": "11999996666"}
    )
    resultado = atualizar_usuario_module.atualizar_usuario.invoke(
        {"usuario_id": criado["id"], "meta_semanal_dias": 5}
    )

    assert resultado["id"] == criado["id"]
    assert resultado["meta_semanal_dias"] == 5


def test_atualizar_usuario_nome(db_session, db_session_factory, monkeypatch):
    monkeypatch.setattr(usuario_criar_module, "SessionLocal", db_session_factory)
    monkeypatch.setattr(atualizar_usuario_module, "SessionLocal", db_session_factory)

    criado = usuario_criar_module.criar_usuario.invoke(
        {"nome": "Diana Tool", "telefone": "11999995555"}
    )
    resultado = atualizar_usuario_module.atualizar_usuario.invoke(
        {"usuario_id": criado["id"], "nome": "Diana Atualizada"}
    )

    assert resultado["name"] == "Diana Atualizada"
    assert resultado["meta_semanal_dias"] == 4  # default não muda


def test_atualizar_usuario_meta_invalida(db_session, db_session_factory, monkeypatch):
    monkeypatch.setattr(usuario_criar_module, "SessionLocal", db_session_factory)
    monkeypatch.setattr(atualizar_usuario_module, "SessionLocal", db_session_factory)

    criado = usuario_criar_module.criar_usuario.invoke(
        {"nome": "Eduardo Tool", "telefone": "11999994444"}
    )
    resultado = atualizar_usuario_module.atualizar_usuario.invoke(
        {"usuario_id": criado["id"], "meta_semanal_dias": 10}
    )

    assert resultado == {"error": "meta_semanal_dias deve ser entre 1 e 7."}


def test_atualizar_usuario_sem_campos_retorna_erro(db_session, db_session_factory, monkeypatch):
    monkeypatch.setattr(usuario_criar_module, "SessionLocal", db_session_factory)
    monkeypatch.setattr(atualizar_usuario_module, "SessionLocal", db_session_factory)

    criado = usuario_criar_module.criar_usuario.invoke(
        {"nome": "Fernanda Tool", "telefone": "11999993333"}
    )
    resultado = atualizar_usuario_module.atualizar_usuario.invoke(
        {"usuario_id": criado["id"]}
    )

    assert resultado == {"error": "Nenhum campo informado para atualização."}


def test_atualizar_usuario_inexistente(db_session, db_session_factory, monkeypatch):
    monkeypatch.setattr(atualizar_usuario_module, "SessionLocal", db_session_factory)

    resultado = atualizar_usuario_module.atualizar_usuario.invoke(
        {"usuario_id": "id-que-nao-existe", "meta_semanal_dias": 3}
    )

    assert resultado == {"error": "Usuário não encontrado."}
