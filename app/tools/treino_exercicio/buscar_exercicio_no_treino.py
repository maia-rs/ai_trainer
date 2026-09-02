"""
Tool para encontrar o treino_exercicio_id de um exercício pelo nome,
buscando nos treinos do usuário. Resolve o problema de match entre o
nome em PT dado pelo usuário e o exercício vinculado ao treino.
"""
from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.exercicio_service import ExercicioService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService


@tool
def buscar_exercicio_no_treino(usuario_id: str, nome_exercicio: str) -> dict:
    """Busca um exercício nos treinos do usuário pelo nome (em português ou inglês)
    e retorna o treino_exercicio_id necessário para registrar a execução.

    Use esta tool ANTES de registrar_execucao_treino quando o usuário informar
    o nome de um exercício. Ela evita ter que chamar múltiplas tools para
    encontrar o treino_exercicio_id correto.

    Exemplos:
    - "puxada alta"       → encontra "lat pulldown" no treino de costas
    - "remada baixa"      → encontra "seated cable row" no treino de costas
    - "cadeira extensora" → encontra "leg extension" no treino de pernas
    - "rosca alternada"   → encontra "dumbbell curl" no treino de braços
    """
    session = SessionLocal()
    try:
        treino_service = TreinoService(session)
        te_service = TreinoExercicioService(session)
        ex_service = ExercicioService(session)

        treinos = treino_service.listar_treinos_por_usuario(usuario_id)
        ativos = [t for t in treinos if t.status == "ativo"]

        # Busca o exercício no catálogo pelo nome
        resultados = ex_service.search_exercicios(nome=nome_exercicio, limite=10)

        if not resultados:
            return {
                "message": f"Nenhum exercício encontrado com o nome '{nome_exercicio}'.",
                "sugestao": "Tente buscar_informacoes_exercicio com termos em inglês.",
            }

        ids_encontrados = {ex.id for ex in resultados}

        # Procura nos treinos ativos qual tem esses exercícios
        matches = []
        for treino in ativos:
            relacoes = te_service.listar_treinos_exercicios_por_treino(treino.id)
            for rel in relacoes:
                if rel.exercicio_id in ids_encontrados:
                    ex = next((e for e in resultados if e.id == rel.exercicio_id), None)
                    matches.append({
                        "treino_exercicio_id": rel.id,
                        "exercicio_id": rel.exercicio_id,
                        "nome_exercicio": ex.nome if ex else rel.exercicio_id,
                        "treino_id": treino.id,
                        "treino_nome": treino.nome,
                        "dia_da_semana": treino.dia_da_semana,
                        "series": rel.series,
                        "repeticoes": rel.repeticoes,
                        "descanso": rel.descanso,
                    })

        if not matches:
            # Retorna os exercícios encontrados no catálogo mas não vinculados a treino
            return {
                "message": f"Exercício '{nome_exercicio}' encontrado no catálogo mas não vinculado a nenhum treino ativo.",
                "exercicios_no_catalogo": [
                    {"id": ex.id, "nome": ex.nome, "equipamento": ex.equipamento}
                    for ex in resultados[:3]
                ],
            }

        return {
            "count": len(matches),
            "matches": matches,
        }

    except ValueError as e:
        return {"error": str(e)}
    finally:
        session.close()
