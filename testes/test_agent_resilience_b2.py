"""
Testes — Bug 2: Deduplicação persistente de webhooks.

Valida que a função _registrar_dedup_db e _mensagem_duplicada usam o banco
como fonte primária de deduplicação, com fallback em memória quando o banco
está indisponível.
"""
import pytest

from app.api.whatsapp import _registrar_dedup_db, _mensagem_duplicada, _mensagens_processadas


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db_session_factory(db_session):
    """Retorna uma factory que sempre entrega a sessão de teste."""
    class _Factory:
        def __call__(self):
            return db_session

    return _Factory()


# ---------------------------------------------------------------------------
# Testes unitários
# ---------------------------------------------------------------------------

def test_dedup_db_novo_message_id(db_session, monkeypatch):
    """Um message_id inédito deve ser registrado no banco e retornar False."""
    monkeypatch.setattr("app.api.whatsapp.SessionLocal", db_session_factory_from(db_session))
    result = _registrar_dedup_db("msg-unique-001")
    assert result is False


def test_dedup_db_detecta_duplicata(db_session, monkeypatch):
    """O mesmo message_id inserido duas vezes deve retornar True na segunda chamada."""
    factory = db_session_factory_from(db_session)
    monkeypatch.setattr("app.api.whatsapp.SessionLocal", factory)

    first = _registrar_dedup_db("msg-dup-002")
    second = _registrar_dedup_db("msg-dup-002")

    assert first is False
    assert second is True


def test_dedup_persiste_apos_reset_dict(db_session, monkeypatch):
    """
    Após registrar via _mensagem_duplicada e limpar o dict em memória,
    a segunda chamada ainda deve detectar duplicata (via banco).
    """
    factory = db_session_factory_from(db_session)
    monkeypatch.setattr("app.api.whatsapp.SessionLocal", factory)

    # Primeira chamada registra no banco e na memória
    first = _mensagem_duplicada("msg-persist-003")
    assert first is False

    # Limpa cache em memória para simular restart / nova instância
    _mensagens_processadas.clear()

    # Segunda chamada deve detectar via banco
    second = _mensagem_duplicada("msg-persist-003")
    assert second is True


def test_dedup_fallback_memoria_quando_banco_falha(monkeypatch):
    """Quando _registrar_dedup_db retorna None (banco indisponível), o dict em memória assume."""
    # Remove qualquer entrada prévia do dict
    _mensagens_processadas.clear()

    monkeypatch.setattr("app.api.whatsapp._registrar_dedup_db", lambda mid: None)

    # Primeira vez: banco falhou, memória não tem → não duplicata
    first = _mensagem_duplicada("msg-fallback-004")
    assert first is False

    # Segunda vez: banco ainda falhou, memória tem → duplicata
    second = _mensagem_duplicada("msg-fallback-004")
    assert second is True


def test_mensagem_nova_nao_duplicada(db_session, monkeypatch):
    """Um message_id completamente inédito deve retornar False em _mensagem_duplicada."""
    factory = db_session_factory_from(db_session)
    monkeypatch.setattr("app.api.whatsapp.SessionLocal", factory)

    result = _mensagem_duplicada("msg-new-005")
    assert result is False


# ---------------------------------------------------------------------------
# Utilitário interno
# ---------------------------------------------------------------------------

def db_session_factory_from(db_session):
    """Cria uma callable que retorna sempre a mesma sessão de teste."""

    class _SessionFactory:
        def __call__(self):
            return db_session

    return _SessionFactory()
