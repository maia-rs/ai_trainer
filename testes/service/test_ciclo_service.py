"""Testes unitários para CicloService.

Cobre requisitos: 3.1–3.4, 4.1–4.5, 5.1, 5.3–5.5, 6.1–6.5, 7.1, 7.3, 7.4, 8.1, 8.2, 11.3, 11.4
"""
import pytest
from datetime import date

from app.schemas.treino import TreinoCreate
from app.schemas.usuario import UsuarioCreate
from app.service.ciclo_service import CicloService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService
from app.schemas.ciclo import CicloResponse, CicloSessaoResponse


# ── Helpers ────────────────────────────────────────────────────────────────────


def _criar_usuario(db_session, telefone="11900000001"):
    return UsuarioService(db_session).criar_usuario(
        UsuarioCreate(name="Usuário Teste", telefone=telefone)
    )


def _criar_treino(db_session, usuario_id, nome="Treino A"):
    return TreinoService(db_session).criar_treino(
        TreinoCreate(
            usuario_id=usuario_id,
            nome=nome,
            descricao=f"Descrição de {nome}",
            dia_da_semana=None,
        )
    )


def _criar_ciclo(db_session, usuario_id, nome="Ciclo Teste", data_inicio=None):
    if data_inicio is None:
        data_inicio = date(2027, 1, 1)
    return CicloService(db_session).criar_ciclo(usuario_id, nome, data_inicio)


# ── Testes de criar_ciclo ──────────────────────────────────────────────────────


def test_criar_ciclo_retorna_status_ativo(db_session):
    """Req 3.1 — ciclo criado sempre tem status=ativo."""
    usuario = _criar_usuario(db_session)
    ciclo = _criar_ciclo(db_session, usuario.id)

    assert isinstance(ciclo, CicloResponse)
    assert ciclo.status == "ativo"
    assert ciclo.usuario_id == usuario.id


def test_criar_ciclo_usuario_inexistente_lanca_value_error(db_session):
    """Req 3.2 — usuário não encontrado deve lançar ValueError."""
    with pytest.raises(ValueError, match="não encontrado"):
        CicloService(db_session).criar_ciclo("id-inexistente", "Ciclo X", date(2027, 1, 1))


def test_criar_segundo_ciclo_ativo_lanca_value_error(db_session):
    """Req 3.3 — dois ciclos ativos para o mesmo usuário não são permitidos."""
    usuario = _criar_usuario(db_session)
    _criar_ciclo(db_session, usuario.id)

    with pytest.raises(ValueError, match="ciclo ativo"):
        _criar_ciclo(db_session, usuario.id, nome="Segundo Ciclo")


# ── Testes de adicionar_sessao ──────────────────────────────────────────────────


def test_adicionar_sessao_valida_retorna_response(db_session):
    """Req 4.1 — sessão válida retorna CicloSessaoResponse."""
    usuario = _criar_usuario(db_session)
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    sessao = CicloService(db_session).adicionar_sessao(ciclo.id, 1, treino.id)

    assert isinstance(sessao, CicloSessaoResponse)
    assert sessao.ciclo_id == ciclo.id
    assert sessao.numero_sessao == 1
    assert sessao.treino_id == treino.id
    assert sessao.concluido is False


def test_adicionar_sessao_ciclo_inexistente_lanca_value_error(db_session):
    """Req 4.2 — ciclo não encontrado lança ValueError."""
    usuario = _criar_usuario(db_session)
    treino = _criar_treino(db_session, usuario.id)

    with pytest.raises(ValueError, match="Ciclo"):
        CicloService(db_session).adicionar_sessao("ciclo-inexistente", 1, treino.id)


def test_adicionar_sessao_treino_inexistente_lanca_value_error(db_session):
    """Req 4.3 — treino não encontrado lança ValueError."""
    usuario = _criar_usuario(db_session)
    ciclo = _criar_ciclo(db_session, usuario.id)

    with pytest.raises(ValueError, match="Treino"):
        CicloService(db_session).adicionar_sessao(ciclo.id, 1, "treino-inexistente")


def test_adicionar_sessao_duplicada_lanca_value_error(db_session):
    """Req 4.4 — (ciclo_id, numero_sessao) duplicado lança ValueError."""
    usuario = _criar_usuario(db_session)
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    svc.adicionar_sessao(ciclo.id, 1, treino.id)

    with pytest.raises(ValueError):
        svc.adicionar_sessao(ciclo.id, 1, treino.id)


def test_adicionar_sessoes_fora_de_ordem_aceitas(db_session):
    """Req 4.5 — sessões inseridas fora de ordem numérica devem ser aceitas."""
    usuario = _criar_usuario(db_session)
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    for numero in [5, 3, 1, 4, 2]:
        svc.adicionar_sessao(ciclo.id, numero, treino.id)

    from app.repositorio.ciclo_sessao import CicloSessaoRepositorio
    sessoes = CicloSessaoRepositorio(db_session).listar_sessoes_por_ciclo(ciclo.id)
    assert len(sessoes) == 5


# ── Testes de obter_proxima_sessao ─────────────────────────────────────────────


def test_obter_proxima_sessao_retorna_menor_numero_sessao(db_session):
    """Req 5.1 — deve retornar a sessão com menor numero_sessao pendente."""
    usuario = _criar_usuario(db_session)
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    for n in [3, 1, 2]:
        svc.adicionar_sessao(ciclo.id, n, treino.id)

    proxima = svc.obter_proxima_sessao(usuario.id)
    assert proxima is not None
    assert proxima["numero_sessao"] == 1


def test_obter_proxima_sessao_sem_ciclo_ativo_retorna_none(db_session):
    """Req 5.3 — sem ciclo ativo deve retornar None."""
    usuario = _criar_usuario(db_session)
    svc = CicloService(db_session)
    assert svc.obter_proxima_sessao(usuario.id) is None


def test_obter_proxima_sessao_todas_concluidas_marca_ciclo_concluido(db_session):
    """Req 5.4 — quando todas as sessões estão concluídas, ciclo vira concluido."""
    usuario = _criar_usuario(db_session)
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    sessao = svc.adicionar_sessao(ciclo.id, 1, treino.id)
    svc.concluir_sessao(sessao.id)

    # Após concluir a única sessão, próxima deve retornar None e ciclo concluído
    proxima = svc.obter_proxima_sessao(usuario.id)
    assert proxima is None

    from app.repositorio.ciclo import CicloRepositorio
    ciclo_atualizado = CicloRepositorio(db_session).obter_ciclo_por_id(ciclo.id)
    assert ciclo_atualizado.status == "concluido"


def test_proxima_sessao_inclui_treino_nome_e_descricao(db_session):
    """Req 5.5 — próxima sessão deve incluir treino_nome e treino_descricao."""
    usuario = _criar_usuario(db_session)
    treino = _criar_treino(db_session, usuario.id, "Treino Força")
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    svc.adicionar_sessao(ciclo.id, 1, treino.id)

    proxima = svc.obter_proxima_sessao(usuario.id)
    assert proxima["treino_nome"] == "Treino Força"
    assert proxima["treino_descricao"] is not None


# ── Testes de concluir_sessao ──────────────────────────────────────────────────


def test_concluir_sessao_valida(db_session):
    """Req 6.1 — sessão concluída tem concluido=True e data_conclusao preenchida."""
    usuario = _criar_usuario(db_session)
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    sessao = svc.adicionar_sessao(ciclo.id, 1, treino.id)
    resultado = svc.concluir_sessao(sessao.id)

    assert resultado.concluido is True
    assert resultado.data_conclusao is not None


def test_concluir_sessao_inexistente_lanca_value_error(db_session):
    """Req 6.2 — sessão não encontrada lança ValueError."""
    with pytest.raises(ValueError, match="Sessão"):
        CicloService(db_session).concluir_sessao("sessao-inexistente")


def test_concluir_sessao_ja_concluida_lanca_value_error(db_session):
    """Req 6.3 — sessão já concluída não pode ser concluída de novo."""
    usuario = _criar_usuario(db_session)
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    sessao = svc.adicionar_sessao(ciclo.id, 1, treino.id)
    svc.concluir_sessao(sessao.id)

    with pytest.raises(ValueError, match="conclu"):
        svc.concluir_sessao(sessao.id)


def test_concluir_ultima_sessao_marca_ciclo_concluido(db_session):
    """Req 6.4 — concluir a última sessão pendente deve marcar ciclo como concluido."""
    usuario = _criar_usuario(db_session)
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    s1 = svc.adicionar_sessao(ciclo.id, 1, treino.id)
    s2 = svc.adicionar_sessao(ciclo.id, 2, treino.id)

    svc.concluir_sessao(s1.id)
    svc.concluir_sessao(s2.id)

    from app.repositorio.ciclo import CicloRepositorio
    ciclo_final = CicloRepositorio(db_session).obter_ciclo_por_id(ciclo.id)
    assert ciclo_final.status == "concluido"


# ── Testes de obter_progresso_ciclo ───────────────────────────────────────────


@pytest.mark.parametrize("concluidas,total,esperado", [
    (0, 10, 0.0),
    (5, 10, 50.0),
    (10, 10, 100.0),
    (3, 7, 42.9),
    (60, 60, 100.0),
])
def test_percentual_conclusao(db_session, concluidas, total, esperado):
    """Req 7.1, 7.3 — percentual_conclusao deve ser calculado corretamente."""
    usuario = _criar_usuario(db_session, telefone=f"1190000{total:04d}")
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    sessoes = []
    for n in range(1, total + 1):
        sessoes.append(svc.adicionar_sessao(ciclo.id, n, treino.id))

    for i in range(concluidas):
        svc.concluir_sessao(sessoes[i].id)

    progresso = svc.obter_progresso_ciclo(ciclo.id)
    assert progresso["sessoes_concluidas"] == concluidas
    assert progresso["total_sessoes"] == total
    assert progresso["percentual_conclusao"] == esperado


def test_progresso_sem_sessoes(db_session):
    """Req 7.4 — ciclo sem sessões deve retornar zeros."""
    usuario = _criar_usuario(db_session)
    ciclo = _criar_ciclo(db_session, usuario.id)

    progresso = CicloService(db_session).obter_progresso_ciclo(ciclo.id)
    assert progresso["sessoes_concluidas"] == 0
    assert progresso["total_sessoes"] == 0
    assert progresso["percentual_conclusao"] == 0.0


# ── Testes de listar_ciclos_por_usuario ────────────────────────────────────────


def test_listar_ciclos_ordenado_por_data_inicio_decrescente(db_session):
    """Req 8.1 — ciclos devem ser listados por data_inicio descendente."""
    usuario = _criar_usuario(db_session)
    svc = CicloService(db_session)

    # Cria três ciclos em ordem crescente de data, mas com o ativo sendo o último
    # Para simular múltiplos ciclos, manipulamos os status após criar
    ciclo1 = svc.criar_ciclo(usuario.id, "Ciclo Jan", date(2027, 1, 1))

    from app.repositorio.ciclo import CicloRepositorio
    repo = CicloRepositorio(db_session)
    c1 = repo.obter_ciclo_por_id(ciclo1.id)
    c1.status = "concluido"
    repo.atualizar_ciclo(c1)

    ciclo2 = svc.criar_ciclo(usuario.id, "Ciclo Mar", date(2027, 3, 1))
    c2 = repo.obter_ciclo_por_id(ciclo2.id)
    c2.status = "concluido"
    repo.atualizar_ciclo(c2)

    ciclo3 = svc.criar_ciclo(usuario.id, "Ciclo Jun", date(2027, 6, 1))

    ciclos = svc.listar_ciclos_por_usuario(usuario.id)
    assert len(ciclos) == 3
    datas = [c.data_inicio for c in ciclos]
    assert datas == sorted(datas, reverse=True)


def test_listar_ciclos_sem_ciclos_retorna_lista_vazia(db_session):
    """Req 8.2 — usuário sem ciclos deve retornar lista vazia."""
    usuario = _criar_usuario(db_session)
    ciclos = CicloService(db_session).listar_ciclos_por_usuario(usuario.id)
    assert ciclos == []


# ── Testes parametrizados de idempotência e sequência ─────────────────────────


@pytest.mark.parametrize("n_consultas", [1, 3, 10])
def test_idempotencia_obter_proxima_sessao(db_session, n_consultas):
    """Req 11.3 — N chamadas sem concluir retornam sempre a mesma sessão."""
    usuario = _criar_usuario(db_session, telefone=f"1190001{n_consultas:04d}")
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    for n in range(1, 4):
        svc.adicionar_sessao(ciclo.id, n, treino.id)

    resultados = [svc.obter_proxima_sessao(usuario.id) for _ in range(n_consultas)]
    ids = [r["ciclo_sessao_id"] for r in resultados]
    assert len(set(ids)) == 1


@pytest.mark.parametrize("total_sessoes", [3, 5, 10, 60])
def test_sequencia_numero_sessao_crescente(db_session, total_sessoes):
    """Req 11.4 — números de sessão retornados após conclusões devem ser crescentes."""
    usuario = _criar_usuario(db_session, telefone=f"1190002{total_sessoes:04d}")
    treino = _criar_treino(db_session, usuario.id)
    ciclo = _criar_ciclo(db_session, usuario.id)

    svc = CicloService(db_session)
    for n in range(1, total_sessoes + 1):
        svc.adicionar_sessao(ciclo.id, n, treino.id)

    numeros = []
    while True:
        proxima = svc.obter_proxima_sessao(usuario.id)
        if proxima is None:
            break
        numeros.append(proxima["numero_sessao"])
        svc.concluir_sessao(proxima["ciclo_sessao_id"])

    assert numeros == sorted(numeros)
    assert len(numeros) == total_sessoes
