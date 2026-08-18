from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.avaliacao_fisica import AvaliacaoFisica
from app.models.execucao import Execucao
from app.models.exercicio import Exercicio, StatusExercicio
from app.models.treino import StatusTreino, Treino
from app.models.treino_exercicio import TreinoExercicio
from app.models.usuario import StatusUsuario, Usuario
from app.tipos.telefone_tipo import TelefoneValue


def _dia_semana_pt(data_ref: datetime) -> str:
    dias = [
        "Segunda-feira",
        "Terca-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sabado",
        "Domingo",
    ]
    return dias[data_ref.weekday()]


def _proximo_dia_semana_pt(data_ref: datetime) -> str:
    return _dia_semana_pt(data_ref + timedelta(days=1))


def _buscar_ou_criar_usuario(session) -> Usuario:
    telefone_seed = TelefoneValue("11988887777")
    usuario = session.execute(
        select(Usuario).where(Usuario.telefone == telefone_seed)
    ).scalar_one_or_none()

    if usuario:
        return usuario

    usuario = Usuario(
        name="Usuario Seed Dashboard",
        telefone=telefone_seed,
        status=StatusUsuario.ATIVO.value,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


def _buscar_ou_criar_exercicio(
    session,
    id_externo: str,
    nome: str,
    categoria: str,
    rotulo: str,
    grupo_muscular: str,
    equipamento: str,
    instrucao: str,
    gif_url: str,
) -> Exercicio:
    exercicio = session.execute(
        select(Exercicio).where(Exercicio.id_externo == id_externo)
    ).scalar_one_or_none()

    if exercicio:
        return exercicio

    exercicio = Exercicio(
        id_externo=id_externo,
        nome=nome,
        categoria=categoria,
        rotulo=rotulo,
        grupo_muscular=grupo_muscular,
        equipamento=equipamento,
        instrucao=instrucao,
        gif_url=gif_url,
        status=StatusExercicio.ATIVO.value,
    )
    session.add(exercicio)
    session.commit()
    session.refresh(exercicio)
    return exercicio


def _buscar_ou_criar_treino(
    session,
    usuario_id: str,
    nome: str,
    descricao: str,
    dia_da_semana: str,
) -> Treino:
    treino = session.execute(
        select(Treino).where(Treino.usuario_id == usuario_id, Treino.nome == nome)
    ).scalar_one_or_none()

    if treino:
        if treino.status != StatusTreino.ATIVO.value:
            treino.status = StatusTreino.ATIVO.value
            session.commit()
            session.refresh(treino)
        return treino

    treino = Treino(
        usuario_id=usuario_id,
        nome=nome,
        descricao=descricao,
        dia_da_semana=dia_da_semana,
        status=StatusTreino.ATIVO.value,
    )
    session.add(treino)
    session.commit()
    session.refresh(treino)
    return treino


def _buscar_ou_criar_treino_exercicio(
    session,
    treino_id: str,
    exercicio_id: str,
    series: int,
    repeticoes: int,
    tempo_descanso: int,
    observacoes: str,
) -> TreinoExercicio:
    relacao = session.execute(
        select(TreinoExercicio).where(
            TreinoExercicio.treino_id == treino_id,
            TreinoExercicio.exercicio_id == exercicio_id,
        )
    ).scalar_one_or_none()

    if relacao:
        return relacao

    relacao = TreinoExercicio(
        treino_id=treino_id,
        exercicio_id=exercicio_id,
        series=series,
        repeticoes=repeticoes,
        tempo_descanso=tempo_descanso,
        observacoes=observacoes,
    )
    session.add(relacao)
    session.commit()
    session.refresh(relacao)
    return relacao


def _buscar_ou_criar_execucao(
    session,
    treino_exercicio_id: str,
    data_execucao: datetime,
    carga: int,
    series_realizadas: int,
    repeticoes_realizadas: int,
    tempo_descanso_real: int,
    duracao_execucao: int,
    calorias_queimadas: int,
    frequencia_cardiaca_media: int,
    observacoes: str,
) -> Execucao:
    execucao = session.execute(
        select(Execucao).where(
            Execucao.treino_exercicio_id == treino_exercicio_id,
            Execucao.data_execucao == data_execucao,
        )
    ).scalar_one_or_none()

    if execucao:
        return execucao

    execucao = Execucao(
        treino_exercicio_id=treino_exercicio_id,
        data_execucao=data_execucao,
        carga=carga,
        series_realizadas=series_realizadas,
        repeticoes_realizadas=repeticoes_realizadas,
        tempo_descanso_real=tempo_descanso_real,
        duracao_execucao=duracao_execucao,
        calorias_queimadas=calorias_queimadas,
        frequencia_cardiaca_media=frequencia_cardiaca_media,
        observacoes=observacoes,
    )
    session.add(execucao)
    session.commit()
    session.refresh(execucao)
    return execucao


def _buscar_ou_criar_avaliacao(
    session,
    usuario_id: str,
    data_avaliacao: datetime,
    peso: float,
    altura: float,
    percentual_gordura: float,
    massa_gorda: float,
    massa_muscular: float,
    imc: float,
    gordura_visceral: float,
    agua_corporal: float,
    taxa_metabolica_basal: float,
    observacoes: str,
) -> AvaliacaoFisica:
    avaliacao = session.execute(
        select(AvaliacaoFisica).where(
            AvaliacaoFisica.usuario_id == usuario_id,
            AvaliacaoFisica.data_avaliacao == data_avaliacao,
        )
    ).scalar_one_or_none()

    if avaliacao:
        return avaliacao

    avaliacao = AvaliacaoFisica(
        usuario_id=usuario_id,
        data_avaliacao=data_avaliacao,
        peso=peso,
        altura=altura,
        percentual_gordura=percentual_gordura,
        massa_gorda=massa_gorda,
        massa_muscular=massa_muscular,
        imc=imc,
        gordura_visceral=gordura_visceral,
        agua_corporal=agua_corporal,
        taxa_metabolica_basal=taxa_metabolica_basal,
        observacoes=observacoes,
    )
    session.add(avaliacao)
    session.commit()
    session.refresh(avaliacao)
    return avaliacao


def seed_dashboard_mysql() -> None:
    agora = datetime.now(timezone.utc)
    hoje_18h = agora.replace(hour=18, minute=0, second=0, microsecond=0)

    with SessionLocal() as session:
        usuario = _buscar_ou_criar_usuario(session)

        exercicio_1 = _buscar_ou_criar_exercicio(
            session,
            id_externo="seed-dashboard-ex-001",
            nome="Supino Reto",
            categoria="Peito",
            rotulo="Supino",
            grupo_muscular="Peitoral",
            equipamento="Barra",
            instrucao="Desca a barra ate a linha media do peito e suba com controle.",
            gif_url="https://example.com/supino-reto.gif",
        )
        exercicio_2 = _buscar_ou_criar_exercicio(
            session,
            id_externo="seed-dashboard-ex-002",
            nome="Agachamento Livre",
            categoria="Pernas",
            rotulo="Agachamento",
            grupo_muscular="Quadriceps",
            equipamento="Barra",
            instrucao="Mantenha coluna neutra e joelhos alinhados durante todo o movimento.",
            gif_url="https://example.com/agachamento-livre.gif",
        )
        exercicio_3 = _buscar_ou_criar_exercicio(
            session,
            id_externo="seed-dashboard-ex-003",
            nome="Remada Curvada",
            categoria="Costas",
            rotulo="Remada",
            grupo_muscular="Dorsal",
            equipamento="Barra",
            instrucao="Puxe a barra em direcao ao abdome mantendo o tronco firme.",
            gif_url="https://example.com/remada-curvada.gif",
        )

        treino_hoje = _buscar_ou_criar_treino(
            session,
            usuario_id=usuario.id,
            nome="Treino Seed - Hoje",
            descricao="Treino principal usado para validar o dashboard no Postman.",
            dia_da_semana=_dia_semana_pt(agora),
        )
        treino_amanha = _buscar_ou_criar_treino(
            session,
            usuario_id=usuario.id,
            nome="Treino Seed - Proximo Dia",
            descricao="Treino secundario para validar listagem de treinos ativos.",
            dia_da_semana=_proximo_dia_semana_pt(agora),
        )

        relacao_1 = _buscar_ou_criar_treino_exercicio(
            session,
            treino_id=treino_hoje.id,
            exercicio_id=exercicio_1.id,
            series=4,
            repeticoes=10,
            tempo_descanso=90,
            observacoes="Carga progressiva.",
        )
        relacao_2 = _buscar_ou_criar_treino_exercicio(
            session,
            treino_id=treino_hoje.id,
            exercicio_id=exercicio_2.id,
            series=4,
            repeticoes=8,
            tempo_descanso=120,
            observacoes="Amplitude completa.",
        )
        _ = _buscar_ou_criar_treino_exercicio(
            session,
            treino_id=treino_amanha.id,
            exercicio_id=exercicio_3.id,
            series=3,
            repeticoes=12,
            tempo_descanso=75,
            observacoes="Foco em tecnica.",
        )

        _buscar_ou_criar_execucao(
            session,
            treino_exercicio_id=relacao_1.id,
            data_execucao=hoje_18h - timedelta(days=2),
            carga=55,
            series_realizadas=4,
            repeticoes_realizadas=10,
            tempo_descanso_real=90,
            duracao_execucao=1100,
            calorias_queimadas=160,
            frequencia_cardiaca_media=124,
            observacoes="Execucao estavel.",
        )
        _buscar_ou_criar_execucao(
            session,
            treino_exercicio_id=relacao_1.id,
            data_execucao=hoje_18h - timedelta(days=1),
            carga=57,
            series_realizadas=4,
            repeticoes_realizadas=10,
            tempo_descanso_real=85,
            duracao_execucao=1080,
            calorias_queimadas=168,
            frequencia_cardiaca_media=126,
            observacoes="Leve progresso de carga.",
        )
        _buscar_ou_criar_execucao(
            session,
            treino_exercicio_id=relacao_2.id,
            data_execucao=hoje_18h - timedelta(days=1),
            carga=70,
            series_realizadas=4,
            repeticoes_realizadas=8,
            tempo_descanso_real=120,
            duracao_execucao=1300,
            calorias_queimadas=190,
            frequencia_cardiaca_media=130,
            observacoes="Boa intensidade.",
        )

        avaliacao_1 = _buscar_ou_criar_avaliacao(
            session,
            usuario_id=usuario.id,
            data_avaliacao=hoje_18h - timedelta(days=30),
            peso=80.2,
            altura=178.0,
            percentual_gordura=17.1,
            massa_gorda=13.7,
            massa_muscular=33.2,
            imc=25.3,
            gordura_visceral=8.0,
            agua_corporal=42.0,
            taxa_metabolica_basal=1680.0,
            observacoes="Ponto inicial do ciclo.",
        )
        avaliacao_2 = _buscar_ou_criar_avaliacao(
            session,
            usuario_id=usuario.id,
            data_avaliacao=hoje_18h - timedelta(days=1),
            peso=78.9,
            altura=178.0,
            percentual_gordura=15.8,
            massa_gorda=12.5,
            massa_muscular=34.1,
            imc=24.9,
            gordura_visceral=7.0,
            agua_corporal=43.3,
            taxa_metabolica_basal=1710.0,
            observacoes="Melhora geral de composicao.",
        )

        print("Seed MySQL concluido com sucesso.")
        print("Use este usuario_id no Postman:", usuario.id)
        print("treino_id (hoje):", treino_hoje.id)
        print("treino_id (proximo dia):", treino_amanha.id)
        print("avaliacao_id (mais recente):", avaliacao_2.id)
        print("avaliacao_id (anterior):", avaliacao_1.id)
        print("Exercicios seed:", exercicio_1.id, exercicio_2.id, exercicio_3.id)


if __name__ == "__main__":
    seed_dashboard_mysql()