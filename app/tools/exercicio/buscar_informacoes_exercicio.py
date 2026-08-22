from langchain_core.tools import tool

from app.core.database import SessionLocal
from app.service.exercicio_service import ExercicioService


@tool
def buscar_informacoes_exercicio(consultas: list[str], limite: int = 5) -> dict:
    """Busca exercicios no catalogo interno por nome, categoria, rotulo,
    grupo muscular ou equipamento.

    O catalogo armazena os nomes dos exercicios em INGLES. Sempre inclua o
    nome em ingles na lista de consultas. Quando o usuario digitar em portugues,
    traduza para ingles e coloque ambos na lista.

    Parametro `consultas`: lista de termos de busca (em ingles e/ou portugues).
    A busca retorna exercicios que combinem com QUALQUER um dos termos.

    Exemplos de uso:
      - usuario diz "pullover com halter"
        -> consultas=["dumbbell pullover", "pullover"]
      - usuario diz "elevação frontal"
        -> consultas=["front raise", "elevacao frontal"]
      - usuario diz "agachamento"
        -> consultas=["squat", "agachamento"]
      - usuario diz "abdominal 3/4"
        -> consultas=["3/4 sit-up", "sit-up", "crunch"]
      - usuario diz "rosca direta"
        -> consultas=["barbell curl", "dumbbell curl", "bicep curl"]
    """
    if not consultas:
        return {"error": "Informe ao menos um termo de busca."}

    session = SessionLocal()

    try:
        exercicio_service = ExercicioService(session)
        vistos: set[str] = set()
        itens = []

        for consulta in consultas:
            if not consulta or not consulta.strip():
                continue
            try:
                resultados = exercicio_service.search_exercicios(
                    nome=consulta.strip(),
                    limite=max(limite, 1),
                )
                for item in resultados:
                    if item.id not in vistos:
                        vistos.add(item.id)
                        itens.append(
                            {
                                "id": item.id,
                                "id_externo": item.id_externo,
                                "nome": item.nome,
                                "categoria": item.categoria,
                                "grupo_muscular": item.grupo_muscular,
                                "equipamento": item.equipamento,
                                "instrucao": item.instrucao,
                                "gif_url": item.gif_url,
                            }
                        )
            except ValueError:
                continue

        if not itens:
            return {
                "message": (
                    "Nenhum exercicio encontrado. Tente outros termos em ingles "
                    "— os nomes no catalogo estao em ingles (ex: 'squat', 'bench press', "
                    "'deadlift', 'pull-up', 'front raise', 'sit-up')."
                )
            }

        # Limita o total ao `limite` solicitado
        itens = itens[:limite]
        return {"count": len(itens), "items": itens}

    finally:
        session.close()