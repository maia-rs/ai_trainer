"""
Seed de dados de demonstração para o usuário Rodrigo Maia.
Popula treinos, execuções e avaliações físicas para visualização do dashboard.

Uso:
    python -m app.tools.seed.seed_rodrigo
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.avaliacao_fisica import AvaliacaoFisica
from app.models.execucao import Execucao
from app.models.exercicio import Exercicio, StatusExercicio
from app.models.treino import Treino, StatusTreino
from app.models.treino_exercicio import TreinoExercicio
from app.models.usuario import Usuario
from app.tipos.telefone_tipo import TelefoneValue

USUARIO_ID = "1cb625ba-99d7-4dc1-9eda-1449c465b6bb"

DIAS_SEMANA = [
    "Segunda-feira",
    "Terca-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sabado",
    "Domingo",
]


def _dia_hoje() -> str:
    return DIAS_SEMANA[datetime.now(timezone.utc).weekday()]


def _dia_amanha() -> str:
    return DIAS_SEMANA[(datetime.now(timezone.utc).weekday() + 1) % 7]


def _buscar_ou_criar_exercicio(session, id_externo, nome, categoria, rotulo, grupo_muscular, equipamento, instrucao, gif_url) -> Exercicio:
    ex = session.execute(select(Exercicio).where(Exercicio.id_externo == id_externo)).scalar_one_or_none()
    if ex:
        return ex
    ex = Exercicio(
        id_externo=id_externo, nome=nome, categoria=categoria, rotulo=rotulo,
        grupo_muscular=grupo_muscular, equipamento=equipamento,
        instrucao=instrucao, gif_url=gif_url, status=StatusExercicio.ATIVO.value,
    )
    session.add(ex)
    session.flush()
    return ex


def _buscar_ou_criar_treino(session, usuario_id, nome, descricao, dia) -> Treino:
    t = session.execute(
        select(Treino).where(Treino.usuario_id == usuario_id, Treino.nome == nome)
    ).scalar_one_or_none()
    if t:
        t.status = StatusTreino.ATIVO.value
        t.dia_da_semana = dia
        return t
    t = Treino(usuario_id=usuario_id, nome=nome, descricao=descricao,
               dia_da_semana=dia, status=StatusTreino.ATIVO.value)
    session.add(t)
    session.flush()
    return t


def _buscar_ou_criar_te(session, treino_id, exercicio_id, series, repeticoes, descanso, obs) -> TreinoExercicio:
    te = session.execute(
        select(TreinoExercicio).where(
            TreinoExercicio.treino_id == treino_id,
            TreinoExercicio.exercicio_id == exercicio_id,
        )
    ).scalar_one_or_none()
    if te:
        return te
    te = TreinoExercicio(treino_id=treino_id, exercicio_id=exercicio_id,
                         series=series, repeticoes=repeticoes,
                         tempo_descanso=descanso, observacoes=obs)
    session.add(te)
    session.flush()
    return te


def seed_rodrigo() -> None:
    agora = datetime.now(timezone.utc)

    with SessionLocal() as session:

        # ── Exercícios ────────────────────────────────────────────────────
        ex_supino = _buscar_ou_criar_exercicio(
            session, "seed-rod-001", "barbell bench press", "Peito", "Peitoral",
            "Peitoral", "Barra",
            "Deite no banco, desça a barra até o peito e empurre de volta ao topo.",
            "http://localhost:8000/exercises/videos/0084-lqd6K0k.gif",
        )
        ex_agach = _buscar_ou_criar_exercicio(
            session, "seed-rod-002", "barbell squat", "Pernas", "Quadríceps",
            "Quadríceps", "Barra",
            "Pés na largura dos ombros, desça até as coxas ficarem paralelas ao chão.",
            "http://localhost:8000/exercises/videos/0043-WRFYOS7.gif",
        )
        ex_remada = _buscar_ou_criar_exercicio(
            session, "seed-rod-003", "barbell bent over row", "Costas", "Dorsais",
            "Dorsais", "Barra",
            "Incline o tronco, puxe a barra em direção ao abdome mantendo as costas retas.",
            "http://localhost:8000/exercises/videos/0059-Wy06JNE.gif",
        )
        ex_desenvolvimento = _buscar_ou_criar_exercicio(
            session, "seed-rod-004", "dumbbell shoulder press", "Ombros", "Deltoides",
            "Deltoides", "Haltere",
            "Sentado ou em pé, empurre os halteres acima da cabeça até os braços ficarem estendidos.",
            "http://localhost:8000/exercises/videos/0393-hzQLNq3.gif",
        )
        ex_pull = _buscar_ou_criar_exercicio(
            session, "seed-rod-005", "pull-up", "Costas", "Dorsais",
            "Dorsais", "Peso Corporal",
            "Suspenda o corpo na barra puxando até o queixo ultrapassar a altura da barra.",
            "http://localhost:8000/exercises/videos/0651-GmzwRHX.gif",
        )
        ex_triceps = _buscar_ou_criar_exercicio(
            session, "seed-rod-006", "cable triceps pushdown", "Braços", "Tríceps",
            "Tríceps", "Cabo",
            "Puxe o cabo para baixo estendendo os cotovelos completamente, mantendo os cotovelos fixos.",
            "http://localhost:8000/exercises/videos/0872-l8V0Wnj.gif",
        )
        ex_rosca = _buscar_ou_criar_exercicio(
            session, "seed-rod-007", "dumbbell curl", "Braços", "Bíceps",
            "Bíceps", "Haltere",
            "Com as palmas voltadas para cima, flexione os cotovelos trazendo os halteres até os ombros.",
            "http://localhost:8000/exercises/videos/0299-G6FT0Zt.gif",
        )
        ex_leg = _buscar_ou_criar_exercicio(
            session, "seed-rod-008", "leg press", "Pernas", "Quadríceps",
            "Quadríceps", "Máquina de Alavanca",
            "Empurre a plataforma com os pés até as pernas ficarem quase estendidas.",
            "http://localhost:8000/exercises/videos/0574-7VwDJMj.gif",
        )

        # ── Treinos ───────────────────────────────────────────────────────
        dia_hoje  = _dia_hoje()
        dia_aman  = _dia_amanha()
        dia_3 = DIAS_SEMANA[(datetime.now(timezone.utc).weekday() + 2) % 7]
        dia_4 = DIAS_SEMANA[(datetime.now(timezone.utc).weekday() + 3) % 7]

        treino_a = _buscar_ou_criar_treino(
            session, USUARIO_ID,
            "Treino A — Peito e Tríceps",
            "Foco em peitoral com trabalho complementar de tríceps.",
            dia_hoje,
        )
        treino_b = _buscar_ou_criar_treino(
            session, USUARIO_ID,
            "Treino B — Costas e Bíceps",
            "Puxadas e remadas com isolamento de bíceps.",
            dia_aman,
        )
        treino_c = _buscar_ou_criar_treino(
            session, USUARIO_ID,
            "Treino C — Pernas",
            "Agachamento, leg press e trabalho de posterior.",
            dia_3,
        )
        treino_d = _buscar_ou_criar_treino(
            session, USUARIO_ID,
            "Treino D — Ombros",
            "Desenvolvimento e elevações.",
            dia_4,
        )

        # ── TreinoExercicio ───────────────────────────────────────────────
        te_supino  = _buscar_ou_criar_te(session, treino_a.id, ex_supino.id,       4, 10, 90, "Carga progressiva")
        te_triceps = _buscar_ou_criar_te(session, treino_a.id, ex_triceps.id,      3, 12, 60, "Cotovelos fixos")
        te_pull    = _buscar_ou_criar_te(session, treino_b.id, ex_pull.id,         4,  8, 90, "Amplitude completa")
        te_remada  = _buscar_ou_criar_te(session, treino_b.id, ex_remada.id,       4, 10, 75, "Tronco estável")
        te_rosca   = _buscar_ou_criar_te(session, treino_b.id, ex_rosca.id,        3, 12, 60, "Supinação no topo")
        te_agach   = _buscar_ou_criar_te(session, treino_c.id, ex_agach.id,        5,  5,120, "5x5 força")
        te_leg     = _buscar_ou_criar_te(session, treino_c.id, ex_leg.id,          3, 15, 75, "Amplitude total")
        te_desenv  = _buscar_ou_criar_te(session, treino_d.id, ex_desenvolvimento.id, 4, 10, 75, "Controle na descida")

        session.commit()

        # ── Execuções — últimos 60 dias ───────────────────────────────────
        random.seed(42)

        # Mapeamento treino_exercicio → carga base e progressão
        config_exec = [
            (te_supino,  60, 2.5),
            (te_triceps, 25, 1.0),
            (te_pull,     0, 0.0),   # peso corporal
            (te_remada,  50, 2.5),
            (te_rosca,   14, 0.5),
            (te_agach,   80, 5.0),
            (te_leg,    100, 5.0),
            (te_desenv,  20, 1.0),
        ]

        # Gera sessões a cada 2-3 dias nos últimos 60 dias
        dias_treino = []
        d = agora - timedelta(days=60)
        while d < agora - timedelta(days=1):
            dias_treino.append(d)
            d += timedelta(days=random.randint(2, 3))

        for i, dia in enumerate(dias_treino):
            # Alterna entre os 4 grupos de exercícios
            grupo = i % 4
            if grupo == 0:
                tes = [(te_supino, 60, 2.5), (te_triceps, 25, 1.0)]
            elif grupo == 1:
                tes = [(te_pull, 0, 0.0), (te_remada, 50, 2.5), (te_rosca, 14, 0.5)]
            elif grupo == 2:
                tes = [(te_agach, 80, 5.0), (te_leg, 100, 5.0)]
            else:
                tes = [(te_desenv, 20, 1.0)]

            for te, carga_base, progressao in tes:
                # Progressão de carga ao longo do tempo
                progresso = round((i / max(len(dias_treino), 1)) * progressao * 8, 1)
                carga = carga_base + progresso + random.uniform(-1, 1)
                carga = max(0, round(carga, 0))

                # Verifica se execução já existe
                data_ex = dia.replace(hour=18, minute=0, second=0, microsecond=0)
                existente = session.execute(
                    select(Execucao).where(
                        Execucao.treino_exercicio_id == te.id,
                        Execucao.data_execucao == data_ex,
                    )
                ).scalar_one_or_none()
                if existente:
                    continue

                ex = Execucao(
                    treino_exercicio_id=te.id,
                    data_execucao=data_ex,
                    carga=int(carga),
                    series_realizadas=te.series,
                    repeticoes_realizadas=te.repeticoes,
                    tempo_descanso_real=te.tempo_descanso + random.randint(-10, 20),
                    duracao_execucao=random.randint(900, 1800),
                    calorias_queimadas=random.randint(120, 250),
                    frequencia_cardiaca_media=random.randint(118, 145),
                    observacoes=None,
                )
                session.add(ex)

        session.commit()

        # ── Avaliações físicas — 1 por mês nos últimos 5 meses ───────────
        avaliacoes_base = [
            # (dias_atras, peso, gordura, muscular)
            (150, 84.5, 19.2, 32.1),
            (120, 83.1, 18.4, 32.8),
            ( 90, 81.7, 17.6, 33.4),
            ( 60, 80.2, 16.8, 34.1),
            ( 30, 79.0, 16.1, 34.7),
            (  5, 78.1, 15.5, 35.2),
        ]

        for dias_atras, peso, gordura, muscular in avaliacoes_base:
            data_av = (agora - timedelta(days=dias_atras)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            existente = session.execute(
                select(AvaliacaoFisica).where(
                    AvaliacaoFisica.usuario_id == USUARIO_ID,
                    AvaliacaoFisica.data_avaliacao == data_av,
                )
            ).scalar_one_or_none()
            if existente:
                continue

            imc = round(peso / (1.78 ** 2), 1)
            massa_gorda = round(peso * gordura / 100, 1)
            av = AvaliacaoFisica(
                usuario_id=USUARIO_ID,
                data_avaliacao=data_av,
                peso=peso,
                altura=178.0,
                percentual_gordura=gordura,
                massa_gorda=massa_gorda,
                massa_muscular=muscular,
                imc=imc,
                gordura_visceral=round(gordura * 0.45, 1),
                agua_corporal=round(60 - gordura * 0.8, 1),
                taxa_metabolica_basal=round(1500 + muscular * 10, 0),
                observacoes="Avaliação periódica",
            )
            session.add(av)

        session.commit()
        print("Seed concluído para Rodrigo Maia!")
        print(f"usuario_id: {USUARIO_ID}")


if __name__ == "__main__":
    seed_rodrigo()
