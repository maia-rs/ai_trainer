"""
Pipeline de ingestão do catálogo de exercícios.

Lê o arquivo exercises-dataset/data/exercises_ptbr.json e realiza
upsert na tabela de exercícios com base no id_externo.

Uso:
    python -m app.tools.seed.seed_exercicios
"""

from __future__ import annotations

import json
import os

from sqlalchemy import select

from app.core import config
from app.core.database import SessionLocal
from app.models.exercicio import Exercicio, StatusExercicio

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
_DATASET_PATH = os.path.join(_ROOT, "exercises-dataset", "data", "exercises_ptbr.json")

# ---------------------------------------------------------------------------
# Dicionários de tradução para campos categóricos
# ---------------------------------------------------------------------------

BODY_PART_PT: dict[str, str] = {
    "back": "Costas",
    "cardio": "Cardio",
    "chest": "Peito",
    "lower arms": "Antebraço",
    "lower legs": "Perna Inferior",
    "neck": "Pescoço",
    "shoulders": "Ombros",
    "upper arms": "Braços",
    "upper legs": "Perna Superior",
    "waist": "Abdômen",
}

EQUIPMENT_PT: dict[str, str] = {
    "assisted": "Assistido",
    "band": "Elástico",
    "barbell": "Barra",
    "body weight": "Peso Corporal",
    "bosu ball": "Bosu",
    "cable": "Cabo",
    "dumbbell": "Haltere",
    "elliptical machine": "Elíptico",
    "ez barbell": "Barra EZ",
    "hammer": "Martelo",
    "kettlebell": "Kettlebell",
    "leverage machine": "Máquina de Alavanca",
    "medicine ball": "Bola Medicinal",
    "olympic barbell": "Barra Olímpica",
    "resistance band": "Faixa de Resistência",
    "roller": "Rolo",
    "rope": "Corda",
    "skierg machine": "SkiErg",
    "sled machine": "Trenó",
    "smith machine": "Smith",
    "stability ball": "Bola de Estabilidade",
    "stationary bike": "Bicicleta Estacionária",
    "stepmill machine": "Escada Rolante",
    "tire": "Pneu",
    "trap bar": "Barra Trap",
    "upper body ergometer": "Ergômetro de Braços",
    "weighted": "Com Peso",
    "wheel roller": "Roda Abdominal",
}

MUSCLE_GROUP_PT: dict[str, str] = {
    "abdominals": "Abdominais",
    "ankle stabilizers": "Estabilizadores do Tornozelo",
    "ankles": "Tornozelos",
    "biceps": "Bíceps",
    "calves": "Panturrilha",
    "chest": "Peitoral",
    "core": "Core",
    "deltoids": "Deltoides",
    "forearms": "Antebraço",
    "glutes": "Glúteos",
    "hamstrings": "Isquiotibiais",
    "hands": "Mãos",
    "hip flexors": "Flexores do Quadril",
    "latissimus dorsi": "Latíssimo do Dorso",
    "lats": "Dorsais",
    "lower back": "Lombar",
    "obliques": "Oblíquos",
    "quadriceps": "Quadríceps",
    "rhomboids": "Romboides",
    "rotator cuff": "Manguito Rotador",
    "shoulders": "Ombros",
    "soleus": "Sóleo",
    "trapezius": "Trapézio",
    "traps": "Trapézio",
    "triceps": "Tríceps",
    "upper back": "Parte Superior das Costas",
    "wrist extensors": "Extensores do Punho",
    "wrist flexors": "Flexores do Punho",
    "wrists": "Punhos",
}

TARGET_PT: dict[str, str] = {
    "abductors": "Abdutores",
    "abs": "Abdominais",
    "adductors": "Adutores",
    "biceps": "Bíceps",
    "calves": "Panturrilha",
    "cardiovascular system": "Sistema Cardiovascular",
    "delts": "Deltoides",
    "forearms": "Antebraço",
    "glutes": "Glúteos",
    "hamstrings": "Isquiotibiais",
    "lats": "Dorsais",
    "levator scapulae": "Levantador da Escápula",
    "pectorals": "Peitoral",
    "quads": "Quadríceps",
    "serratus anterior": "Serrátil Anterior",
    "spine": "Coluna",
    "traps": "Trapézio",
    "triceps": "Tríceps",
    "upper back": "Parte Superior das Costas",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _traduzir(dicionario: dict[str, str], valor: str) -> str:
    """Retorna a tradução ou o valor original em título caso não encontre."""
    return dicionario.get(valor.lower(), valor.title())


def _montar_gif_url(gif_path: str) -> str:
    """
    Converte o caminho relativo do dataset (ex: 'videos/0001-2gPfomN.gif')
    para a URL pública servida pelo FastAPI (ex: '{BASE_URL}/exercises/videos/0001-2gPfomN.gif').
    """
    gif_path = gif_path.lstrip("/")
    return f"{config.BASE_URL}/exercises/{gif_path}"


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------


def _upsert_exercicio(session, raw: dict) -> tuple[str, bool]:
    """
    Cria ou atualiza um exercício. Retorna (id_externo, criado).
    """
    id_externo = raw["id"]

    instrucao = raw.get("instructions", {}).get("ptBR") or raw.get("instructions", {}).get("en", "")

    novo = Exercicio(
        id_externo=id_externo,
        nome=raw["name"],
        categoria=_traduzir(BODY_PART_PT, raw.get("body_part", "")),
        rotulo=_traduzir(TARGET_PT, raw.get("target", "")),
        grupo_muscular=_traduzir(MUSCLE_GROUP_PT, raw.get("muscle_group", "")),
        equipamento=_traduzir(EQUIPMENT_PT, raw.get("equipment", "")),
        instrucao=instrucao,
        gif_url=_montar_gif_url(raw["gif_url"]),
        status=StatusExercicio.ATIVO.value,
    )

    existente: Exercicio | None = session.execute(
        select(Exercicio).where(Exercicio.id_externo == id_externo)
    ).scalar_one_or_none()

    if existente:
        # Atualiza todos os campos (exceto id, id_externo e created_at)
        existente.nome = novo.nome
        existente.categoria = novo.categoria
        existente.rotulo = novo.rotulo
        existente.grupo_muscular = novo.grupo_muscular
        existente.equipamento = novo.equipamento
        existente.instrucao = novo.instrucao
        existente.gif_url = novo.gif_url
        existente.status = StatusExercicio.ATIVO.value
        return id_externo, False

    session.add(novo)
    return id_externo, True


def seed_exercicios(batch_size: int = 100) -> None:
    """Executa o pipeline de ingestão completo."""

    print(f"Lendo dataset: {_DATASET_PATH}")
    with open(_DATASET_PATH, encoding="utf-8") as f:
        exercicios = json.load(f)

    total = len(exercicios)
    criados = 0
    atualizados = 0

    print(f"Total de exercícios no dataset: {total}")

    with SessionLocal() as session:
        for i in range(0, total, batch_size):
            lote = exercicios[i : i + batch_size]

            for raw in lote:
                _, foi_criado = _upsert_exercicio(session, raw)
                if foi_criado:
                    criados += 1
                else:
                    atualizados += 1

            session.commit()
            processados = min(i + batch_size, total)
            print(f"  Processados {processados}/{total}...")

    print("\n✅ Ingestão concluída!")
    print(f"   Criados:     {criados}")
    print(f"   Atualizados: {atualizados}")
    print(f"   Total:       {total}")


if __name__ == "__main__":
    seed_exercicios()
