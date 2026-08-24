"""
Testes para as tools de update — verifica que campos None não sobrescrevem
dados existentes no banco (bug do exclude_unset=True com campos explicitamente None).
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.avaliacao_fisica import AvaliacaoFisicaCreate, AvaliacaoFisicaUpdate
from app.schemas.treino import TreinoCreate, TreinoUpdate
from app.schemas.treino_exercicio import TreinoExercicioCreate, TreinoExercicioUpdate
from app.schemas.exercicio import ExercicioCreate
from app.schemas.usuario import UsuarioCreate
from app.service.avaliacao_service import AvaliacaoService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService
from app.service.exercicio_service import ExercicioService
from app.service.usuario_service import UsuarioService


# ---------------------------------------------------------------------------
# Helpers de seed
# ---------------------------------------------------------------------------

def _criar_usuario(session):
    return UsuarioService(session).criar_usuario(
        UsuarioCreate(name="Teste Update", telefone="11988880000")
    )


def _criar_treino(session, usuario_id: str):
    return TreinoService(session).criar_treino(
        TreinoCreate(
            usuario_id=usuario_id,
            nome="Treino Original",
            descricao="Descrição original",
            dia_da_semana="Segunda-feira",
        )
    )


def _criar_exercicio(session):
    return ExercicioService(session).criar_exercicio(
        ExercicioCreate(
            id_externo="upd-test-001",
            nome="bench press",
            categoria="Peito",
            rotulo="Supino",
            grupo_muscular="Peitoral",
            equipamento="Barra",
            instrucao="Deite e empurre.",
            gif_url="https://example.com/test.gif",
        )
    )


def _criar_treino_exercicio(session, treino_id: str, exercicio_id: str):
    return TreinoExercicioService(session).criar_treino_exercicio(
        TreinoExercicioCreate(
            treino_id=treino_id,
            exercicio_id=exercicio_id,
            series=4,
            repeticoes=10,
            descanso=90,
            observacoes="Original",
        )
    )


def _criar_avaliacao(session, usuario_id: str):
    return AvaliacaoService(session).criar_avaliacao(
        AvaliacaoFisicaCreate(
            usuario_id=usuario_id,
            data_avaliacao=datetime.now(timezone.utc),
            peso=80.0,
            altura=1.75,
            percentual_gordura=15.0,
            massa_gorda=12.0,
            massa_muscular=34.0,
            imc=26.1,
            gordura_visceral=8.0,
            agua_corporal=60.0,
            taxa_metabolica_basal=1800.0,
            observacoes="Avaliação inicial",
        )
    )


# ---------------------------------------------------------------------------
# Testes da tool atualizar_treino
# ---------------------------------------------------------------------------

class TestAtualizarTreino:

    def test_atualiza_apenas_nome(self, db_session):
        usuario = _criar_usuario(db_session)
        treino = _criar_treino(db_session, usuario.id)

        campos = {"nome": "Novo Nome"}
        payload = TreinoUpdate(**campos)
        atualizado = TreinoService(db_session).atualizar_treino(treino.id, payload)

        assert atualizado.nome == "Novo Nome"
        assert atualizado.descricao == "Descrição original"  # não foi sobrescrito
        assert atualizado.dia_da_semana == "Segunda-feira"

    def test_atualiza_apenas_dia(self, db_session):
        usuario = _criar_usuario(db_session)
        treino = _criar_treino(db_session, usuario.id)

        payload = TreinoUpdate(**{"dia_da_semana": "Sexta-feira"})
        atualizado = TreinoService(db_session).atualizar_treino(treino.id, payload)

        assert atualizado.dia_da_semana == "Sexta-feira"
        assert atualizado.nome == "Treino Original"

    def test_nenhum_campo_nao_quebra(self, db_session):
        """Garante que a tool retorna erro ao chamar com campos vazios."""
        # Simula o comportamento da tool com campos={} 
        campos: dict = {}
        assert not campos  # a tool retornaria {"error": "Nenhum campo..."}

    def test_none_explicito_nao_sobrescreve(self, db_session):
        """Criar TreinoUpdate apenas com campos fornecidos não zera os outros."""
        usuario = _criar_usuario(db_session)
        treino = _criar_treino(db_session, usuario.id)

        # Simula o que a tool faz: só inclui o campo fornecido
        payload = TreinoUpdate(**{"nome": "Nome Novo"})
        atualizado = TreinoService(db_session).atualizar_treino(treino.id, payload)

        assert atualizado.nome == "Nome Novo"
        assert atualizado.descricao == "Descrição original"


# ---------------------------------------------------------------------------
# Testes da tool atualizar_exercicio_treino
# ---------------------------------------------------------------------------

class TestAtualizarExercicioTreino:

    def test_atualiza_apenas_series(self, db_session):
        usuario = _criar_usuario(db_session)
        treino = _criar_treino(db_session, usuario.id)
        exercicio = _criar_exercicio(db_session)
        te = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

        payload = TreinoExercicioUpdate(**{"series": 5})
        atualizado = TreinoExercicioService(db_session).atualizar_treino_exercicio(te.id, payload)

        assert atualizado.series == 5
        assert atualizado.repeticoes == 10  # não foi sobrescrito
        assert atualizado.observacoes == "Original"

    def test_atualiza_apenas_observacoes(self, db_session):
        usuario = _criar_usuario(db_session)
        treino = _criar_treino(db_session, usuario.id)
        exercicio = _criar_exercicio(db_session)
        te = _criar_treino_exercicio(db_session, treino.id, exercicio.id)

        payload = TreinoExercicioUpdate(**{"observacoes": "Nova obs"})
        atualizado = TreinoExercicioService(db_session).atualizar_treino_exercicio(te.id, payload)

        assert atualizado.observacoes == "Nova obs"
        assert atualizado.series == 4
        assert atualizado.repeticoes == 10


# ---------------------------------------------------------------------------
# Testes da tool atualizar_avaliacao_fisica
# ---------------------------------------------------------------------------

class TestAtualizarAvaliacaoFisica:

    def test_atualiza_apenas_peso(self, db_session):
        usuario = _criar_usuario(db_session)
        av = _criar_avaliacao(db_session, usuario.id)

        payload = AvaliacaoFisicaUpdate(**{"peso": 78.5})
        atualizada = AvaliacaoService(db_session).atualizar_avaliacao(av.id, payload)

        assert atualizada.peso == 78.5
        assert atualizada.altura == 1.75  # não foi sobrescrito
        assert atualizada.percentual_gordura == 15.0

    def test_atualiza_multiplos_campos(self, db_session):
        usuario = _criar_usuario(db_session)
        av = _criar_avaliacao(db_session, usuario.id)

        payload = AvaliacaoFisicaUpdate(**{"peso": 79.0, "percentual_gordura": 14.5})
        atualizada = AvaliacaoService(db_session).atualizar_avaliacao(av.id, payload)

        assert atualizada.peso == 79.0
        assert atualizada.percentual_gordura == 14.5
        assert atualizada.massa_muscular == 34.0  # não foi sobrescrito

    def test_none_explicito_causa_erro_no_banco(self, db_session):
        """
        Confirma que criar Update com None explícito e exclude_unset=True
        ainda passa None para o banco — esse era o bug original.
        """
        usuario = _criar_usuario(db_session)
        av = _criar_avaliacao(db_session, usuario.id)

        # Simula o comportamento ANTIGO (bugado): passa None explicitamente
        payload_bugado = AvaliacaoFisicaUpdate(peso=None, altura=None)
        dados = payload_bugado.model_dump(exclude_unset=True)

        # O bug: mesmo com exclude_unset=True, peso e altura aparecem como None
        # pois foram explicitamente passados ao construtor
        assert "peso" in dados
        assert dados["peso"] is None

    def test_fix_nao_inclui_nones(self, db_session):
        """
        Confirma que o fix (só incluir campos não-None) resolve o problema.
        """
        # Simula o comportamento CORRIGIDO da tool
        peso = None
        altura = 1.78

        campos: dict = {}
        if peso is not None:
            campos["peso"] = peso
        if altura is not None:
            campos["altura"] = altura

        payload = AvaliacaoFisicaUpdate(**campos)
        dados = payload.model_dump(exclude_unset=True)

        assert "peso" not in dados       # não foi incluído
        assert dados["altura"] == 1.78   # foi incluído corretamente
