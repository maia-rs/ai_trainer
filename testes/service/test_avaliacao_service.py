from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.avaliacao_fisica import (
    AvaliacaoFisicaCreate,
    AvaliacaoFisicaResponse,
    AvaliacaoFisicaUpdate,
)
from app.schemas.usuario import UsuarioCreate
from app.service.avaliacao_service import AvaliacaoService
from app.service.usuario_service import UsuarioService


def _criar_usuario(db_session, nome: str = "Usuario Avaliacao", telefone: str = "11920000001"):
    return UsuarioService(db_session).criar_usuario(
        UsuarioCreate(name=nome, telefone=telefone)
    )


def _payload_avaliacao(usuario_id: str, data_avaliacao: datetime | None = None) -> AvaliacaoFisicaCreate:
    if data_avaliacao is None:
        data_avaliacao = datetime.now(timezone.utc) - timedelta(days=1)
    return AvaliacaoFisicaCreate(
        usuario_id=usuario_id,
        data_avaliacao=data_avaliacao,
        peso=80.0,
        altura=180.0,
        percentual_gordura=15.5,
        massa_gorda=12.4,
        massa_muscular=38.2,
        imc=24.7,
        gordura_visceral=8.0,
        agua_corporal=42.0,
        taxa_metabolica_basal=1700.0,
        observacoes="Avaliacao inicial",
    )


def test_criar_avaliacao_com_sucesso(db_session):
    usuario = _criar_usuario(db_session)
    service = AvaliacaoService(db_session)

    response = service.criar_avaliacao(_payload_avaliacao(usuario.id))

    assert isinstance(response, AvaliacaoFisicaResponse)
    assert response.usuario_id == usuario.id
    assert response.peso == 80.0
    assert response.percentual_gordura == 15.5


def test_criar_avaliacao_usuario_inexistente(db_session):
    service = AvaliacaoService(db_session)

    with pytest.raises(ValueError, match="Usuário não encontrado"):
        service.criar_avaliacao(_payload_avaliacao("usuario-inexistente"))


def test_criar_avaliacao_valor_negativo(db_session):
    usuario = _criar_usuario(db_session, nome="Usuario Negativo", telefone="11920000002")
    service = AvaliacaoService(db_session)

    payload = _payload_avaliacao(usuario.id)
    payload.peso = -1

    with pytest.raises(ValueError, match="peso"):
        service.criar_avaliacao(payload)


def test_criar_avaliacao_data_futura(db_session):
    usuario = _criar_usuario(db_session, nome="Usuario Futuro", telefone="11920000003")
    service = AvaliacaoService(db_session)

    payload = _payload_avaliacao(
        usuario.id,
        data_avaliacao=datetime.now(timezone.utc) + timedelta(days=1),
    )

    with pytest.raises(ValueError, match="data da avaliação não pode ser futura"):
        service.criar_avaliacao(payload)


def test_obter_avaliacao_por_id(db_session):
    usuario = _criar_usuario(db_session, nome="Usuario Obter", telefone="11920000004")
    service = AvaliacaoService(db_session)

    criada = service.criar_avaliacao(_payload_avaliacao(usuario.id))
    obtida = service.obter_avaliacao_por_id(criada.id)

    assert obtida is not None
    assert obtida.id == criada.id
    assert obtida.usuario_id == usuario.id


def test_listar_avaliacoes_por_usuario(db_session):
    usuario = _criar_usuario(db_session, nome="Usuario Listar", telefone="11920000005")
    service = AvaliacaoService(db_session)

    service.criar_avaliacao(_payload_avaliacao(usuario.id, datetime.now(timezone.utc) - timedelta(days=2)))
    service.criar_avaliacao(_payload_avaliacao(usuario.id, datetime.now(timezone.utc) - timedelta(days=1)))

    avaliacoes = service.listar_avaliacoes_por_usuario(usuario.id)

    assert len(avaliacoes) == 2
    assert all(avaliacao.usuario_id == usuario.id for avaliacao in avaliacoes)


def test_obter_ultima_avaliacao_por_usuario(db_session):
    usuario = _criar_usuario(db_session, nome="Usuario Ultima", telefone="11920000006")
    service = AvaliacaoService(db_session)

    antiga = service.criar_avaliacao(_payload_avaliacao(usuario.id, datetime.now(timezone.utc) - timedelta(days=5)))
    ultima = service.criar_avaliacao(_payload_avaliacao(usuario.id, datetime.now(timezone.utc) - timedelta(days=1)))

    obtida = service.obter_ultima_avaliacao_por_usuario(usuario.id)

    assert obtida.id != antiga.id
    assert obtida.id == ultima.id


def test_atualizar_avaliacao(db_session):
    usuario = _criar_usuario(db_session, nome="Usuario Atualiza", telefone="11920000007")
    service = AvaliacaoService(db_session)

    criada = service.criar_avaliacao(_payload_avaliacao(usuario.id))

    atualizada = service.atualizar_avaliacao(
        criada.id,
        AvaliacaoFisicaUpdate(
            peso=78.0,
            percentual_gordura=14.8,
            observacoes="Melhora apos ciclo",
        ),
    )

    assert atualizada.peso == 78.0
    assert atualizada.percentual_gordura == 14.8
    assert atualizada.observacoes == "Melhora apos ciclo"


def test_atualizar_avaliacao_valor_negativo(db_session):
    usuario = _criar_usuario(db_session, nome="Usuario Neg Update", telefone="11920000008")
    service = AvaliacaoService(db_session)

    criada = service.criar_avaliacao(_payload_avaliacao(usuario.id))

    with pytest.raises(ValueError, match="peso"):
        service.atualizar_avaliacao(criada.id, AvaliacaoFisicaUpdate(peso=-2))


def test_deletar_avaliacao(db_session):
    usuario = _criar_usuario(db_session, nome="Usuario Deleta", telefone="11920000009")
    service = AvaliacaoService(db_session)

    criada = service.criar_avaliacao(_payload_avaliacao(usuario.id))

    assert service.deletar_avaliacao(criada.id) is True
    with pytest.raises(ValueError, match="Avaliação não encontrada"):
        service.obter_avaliacao_por_id(criada.id)
