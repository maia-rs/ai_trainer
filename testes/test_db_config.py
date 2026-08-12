from sqlalchemy import select

from app.models.usuario import Usuario
from app.tipos.telefone_tipo import TelefoneValue


def test_db_session_isolated_sqlite(db_session):
    usuario = Usuario(
        name="Teste",
        telefone=TelefoneValue("11999998888"),
    )

    db_session.add(usuario)
    db_session.commit()

    salvo = db_session.execute(
        select(Usuario).where(Usuario.id == usuario.id)
    ).scalar_one_or_none()

    assert salvo is not None
    assert salvo.name == "Teste"
