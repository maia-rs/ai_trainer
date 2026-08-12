import pytest

from app.schemas.exercicio import ExercicioCreate, ExercicioUpdate
from app.service.exercicio_service import ExercicioService

"""

    id_externo: str = Field(..., max_length=50, description="ID externo do exercício")
    nome: str = Field(..., max_length=100, description="Nome do exercício")
    rotulo: str = Field(..., max_length=100, description="Rótula do exercício")
    grupo_muscular: str = Field(..., max_length=50, description="Grupo muscular do exercício")
    equipamento: str = Field(..., max_length=50, description="Equipamento necessário para o exercício")
    instrucao: str = Field(..., description="Instrução detalhada do exercício")
    gif_url: str = Field(..., description="URL do GIF demonstrativo do exercício")


"""

def test_criar_exercicio_com_sucesso(db_session):
    service = ExercicioService(db_session)

    payload = ExercicioCreate(
        id_externo="ex001",
        nome="Agachamento",
        rotulo="Agachamento com barra",
        grupo_muscular="Pernas",
        equipamento="Barra",
        instrucao="Mantenha a postura correta e agache até 90 graus.",
        gif_url="http://example.com/agachamento.gif"
    )
    exercicio = service.criar_exercicio(payload)
    assert exercicio.id_externo == "ex001"
    assert exercicio.nome == "Agachamento"
    assert exercicio.rotulo == "Agachamento com barra"
    assert exercicio.grupo_muscular == "Pernas"
    assert exercicio.equipamento == "Barra"
    assert exercicio.instrucao == "Mantenha a postura correta e agache até 90 graus."
    assert exercicio.gif_url == "http://example.com/agachamento.gif"    

def test_nao_permite_external_id_duplicado(db_session):
    service = ExercicioService(db_session)

    service.criar_exercicio(ExercicioCreate(
        id_externo="ex001",
        nome="Agachamento",
        rotulo="Agachamento com barra",
        grupo_muscular="Pernas",
        equipamento="Barra",
        instrucao="Mantenha a postura correta e agache até 90 graus.",
        gif_url="http://example.com/agachamento.gif"
    ))

    with pytest.raises(ValueError, match="External ID já cadastrado"):
        service.criar_exercicio(ExercicioCreate(
            id_externo="ex001",
            nome="Supino",
            rotulo="Supino reto",
            grupo_muscular="Peito",
            equipamento="Barra",
            instrucao="Deite no banco e empurre a barra para cima.",
            gif_url="http://example.com/supino.gif"

        ))  
def test_obter_exercicio_por_id(db_session):
    service = ExercicioService(db_session)

    exercicio_criado = service.criar_exercicio(ExercicioCreate(
        id_externo="ex002",
        nome="Supino",
        rotulo="Supino reto",
        grupo_muscular="Peito",
        equipamento="Barra",
        instrucao="Deite no banco e empurre a barra para cima.",
        gif_url="http://example.com/supino.gif"
    ))
    exercicio_obtido = service.obter_exercicio_por_id(exercicio_criado.id)

    assert exercicio_obtido is not None
    assert exercicio_obtido.id == exercicio_criado.id
    assert exercicio_obtido.nome == "Supino"
    assert exercicio_obtido.rotulo == "Supino reto"
    assert exercicio_obtido.grupo_muscular == "Peito"
    assert exercicio_obtido.equipamento == "Barra"
    assert exercicio_obtido.instrucao == "Deite no banco e empurre a barra para cima."
    assert exercicio_obtido.gif_url == "http://example.com/supino.gif"  

def test_obter_exercicio_por_external_id(db_session):
    service = ExercicioService(db_session)

    exercicio_criado = service.criar_exercicio(ExercicioCreate(
        id_externo="ex002",
        nome="Supino",
        rotulo="Supino reto",
        grupo_muscular="Peito",
        equipamento="Barra",
        instrucao="Deite no banco e empurre a barra para cima.",
        gif_url="http://example.com/supino.gif"
    ))
    exercicio_obtido = service.obter_exercicio_por_external_id("ex002")

    assert exercicio_obtido is not None
    assert exercicio_obtido.id == exercicio_criado.id
    assert exercicio_obtido.nome == "Supino"
    assert exercicio_obtido.rotulo == "Supino reto"
    assert exercicio_obtido.grupo_muscular == "Peito"
    assert exercicio_obtido.equipamento == "Barra"
    assert exercicio_obtido.instrucao == "Deite no banco e empurre a barra para cima."
    assert exercicio_obtido.gif_url == "http://example.com/supino.gif"


def test_listar_exercicios(db_session):
    service = ExercicioService(db_session)

    service.criar_exercicio(ExercicioCreate(
        id_externo="ex001",
        nome="Agachamento",
        rotulo="Agachamento com barra",
        grupo_muscular="Pernas",
        equipamento="Barra",
        instrucao="Mantenha a postura correta e agache até 90 graus.",
        gif_url="http://example.com/agachamento.gif"
    ))

    service.criar_exercicio(ExercicioCreate(
        id_externo="ex002",
        nome="Supino",
        rotulo="Supino reto",
        grupo_muscular="Peito",
        equipamento="Barra",
        instrucao="Deite no banco e empurre a barra para cima.",
        gif_url="http://example.com/supino.gif"
    ))

    exercicios = service.listar_exercicios()
    assert len(exercicios) == 2
    assert exercicios[0].nome == "Agachamento"
    assert exercicios[1].nome == "Supino"
    assert exercicios[0].rotulo == "Agachamento com barra"
    assert exercicios[1].rotulo == "Supino reto"
    assert exercicios[0].grupo_muscular == "Pernas"
    assert exercicios[1].grupo_muscular == "Peito"
    assert exercicios[0].equipamento == "Barra"
    assert exercicios[1].equipamento == "Barra"
    assert exercicios[0].instrucao == "Mantenha a postura correta e agache até 90 graus."
    assert exercicios[1].instrucao == "Deite no banco e empurre a barra para cima."
    assert exercicios[0].gif_url == "http://example.com/agachamento.gif"
    assert exercicios[1].gif_url == "http://example.com/supino.gif"


def test_search_exercicios(db_session):
    service = ExercicioService(db_session)

    service.criar_exercicio(ExercicioCreate(
        id_externo="ex001",
        nome="Agachamento",
        rotulo="Agachamento com barra",
        grupo_muscular="Pernas",
        equipamento="Barra",
        instrucao="Mantenha a postura correta e agache até 90 graus.",
        gif_url="http://example.com/agachamento.gif"
    ))

    service.criar_exercicio(ExercicioCreate(
        id_externo="ex002",
        nome="Supino",
        rotulo="Supino reto",
        grupo_muscular="Peito",
        equipamento="Barra",
        instrucao="Deite no banco e empurre a barra para cima.",
        gif_url="http://example.com/supino.gif"
    ))

    resultados = service.search_exercicios("Agachamento")
    assert len(resultados) == 1
    assert resultados[0].nome == "Agachamento"

    resultados = service.search_exercicios("Supino")
    assert len(resultados) == 1
    assert resultados[0].nome == "Supino"

    resultados = service.search_exercicios("Não existente")
    assert len(resultados) == 0


def test_atualizar_exercicio(db_session):
    service = ExercicioService(db_session)

    exercicio_criado = service.criar_exercicio(ExercicioCreate(
        id_externo="ex003",
        nome="Levantamento Terra",
        rotulo="Levantamento Terra com barra",
        grupo_muscular="Costas",
        equipamento="Barra",
        instrucao="Mantenha a postura correta e levante a barra do chão.",
        gif_url="http://example.com/levantamento_terra.gif"
    ))
    
    exercicio_atualizado = service.atualizar_exercicio(exercicio_criado.id, ExercicioUpdate(
        nome="Levantamento Terra",
        rotulo="Levantamento Terra com barra",
        grupo_muscular="Costas",
        equipamento="Barra",
        instrucao="Mantenha a postura correta e levante a barra do chão.",
        gif_url="http://example.com/levantamento_terra_atualizado.gif"
    ))

    assert exercicio_atualizado is not None
    assert exercicio_atualizado.id == exercicio_criado.id
    assert exercicio_atualizado.nome == "Levantamento Terra"
    assert exercicio_atualizado.rotulo == "Levantamento Terra com barra"
    assert exercicio_atualizado.grupo_muscular == "Costas"
    assert exercicio_atualizado.equipamento == "Barra"
    assert exercicio_atualizado.instrucao == "Mantenha a postura correta e levante a barra do chão."
    assert exercicio_atualizado.gif_url == "http://example.com/levantamento_terra_atualizado.gif"


