from app.core.database import SessionLocal
from app.repositorio.treino_exercicio import TreinoExercicioRepositorio
from app.repositorio.exercicio import ExercicioRepositorio
from app.repositorio.execucao import ExecucaoRepositorio
from app.repositorio.avaliacao_fisica import AvaliacaoFisicaRepositorio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

""""
get_weight_progress() - Retornar a evolução do peso corporal em um determinado período.
get_body_fat_progress() - Retornar a evolução do percentual de gordura.
get_muscle_mass_progress() - Retornar a evolução da massa muscular.
get_strength_progress() - Retornar a evolução da carga utilizada em um exercício específico.
get_training_frequency() - Calcular a frequência de treinos do usuário.
get_training_volume() - Calcular o volume total de treino.
get_exercise_progress() - Retornar a evolução de um exercício específico. (carga, repetições, séries, tempo de execução, descanso)
obter_evolucao_treino_dia() - Retornar a evolução do treino do dia, incluindo carga, repetições, séries, tempo de execução e descanso.
compare_physical_evaluations() - Comparar os resultados de duas avaliações físicas diferentes.
get_progress_summary() - Retornar um resumo geral do progresso do usuário, incluindo peso, percentual de gordura, massa muscular, força e frequência de treino.
get_dashboard_metrics() - Retornar métricas gerais para o painel do usuário.

Regras de Negócio:
Os cálculos devem considerar apenas registros válidos.
Os dados devem ser ordenados cronologicamente.
Caso não existam informações suficientes, retornar um resultado apropriado.
O período informado deve ser respeitado em todos os cálculos.
Os indicadores devem ser derivados exclusivamente dos dados armazenados.


"""

class ProgressoService:

    """ Classe de serviço para calcular e fornecer informações sobre o progresso do usuário em relação aos seus treinos e avaliações físicas. """

    def __init__(self, db: Session = SessionLocal()):
        self.db = db
        self.treino_exercicio_repositorio = TreinoExercicioRepositorio(db)
        self.exercicio_repositorio = ExercicioRepositorio(db)
        self.execucao_repositorio = ExecucaoRepositorio(db)
        self.avaliacao_fisica_repositorio = AvaliacaoFisicaRepositorio(db)

    def obter_peso_evolucao(self, data_inicio: datetime, data_fim: datetime):
        """
        Retorna a evolução do peso corporal em um determinado período.
        :param data_inicio: Data de início do período.
        :param data_fim: Data de fim do período.
        :return: Lista de registros de peso ordenados cronologicamente.
        """
        #Verificar se as datas são válidas
        if data_inicio > data_fim:
            raise ValueError("A data de início não pode ser posterior à data de fim.")
        
        avaliacoes = self.avaliacao_fisica_repositorio.obter_avaliacoes_por_periodo(data_inicio, data_fim)
        return sorted(avaliacoes, key=lambda x: x.data_avaliacao)

    def obter_percentual_gordura_evolucao(self, data_inicio: datetime, data_fim: datetime):
        """
        Retorna a evolução do percentual de gordura em um determinado período.
        :param data_inicio: Data de início do período.
        :param data_fim: Data de fim do período.
        :return: Lista de registros de percentual de gordura ordenados cronologicamente.
        """
        #Verificar se as datas são válidas
        if data_inicio > data_fim:
            raise ValueError("A data de início não pode ser posterior à data de fim.")
        
        avaliacoes = self.avaliacao_fisica_repositorio.obter_avaliacoes_por_periodo(data_inicio, data_fim)
        return sorted(avaliacoes, key=lambda x: x.data_avaliacao)

    def obter_massa_muscular_evolucao(self, data_inicio: datetime, data_fim: datetime):
        """
        Retorna a evolução da massa muscular em um determinado período.
        :param data_inicio: Data de início do período.
        :param data_fim: Data de fim do período.
        :return: Lista de registros de massa muscular ordenados cronologicamente.
        """
        #Verificar se as datas são válidas
        if data_inicio > data_fim:
            raise ValueError("A data de início não pode ser posterior à data de fim.")
        
        avaliacoes = self.avaliacao_fisica_repositorio.obter_avaliacoes_por_periodo(data_inicio, data_fim)
        return sorted(avaliacoes, key=lambda x: x.data_avaliacao)

    def obter_forca_evolucao(self, exercicio_id: str, data_inicio: datetime, data_fim: datetime):
        """
        Retorna a evolução da força em um exercício específico em um determinado período.
        :param exercicio_id: ID do exercício.
        :param data_inicio: Data de início do período.
        :param data_fim: Data de fim do período.
        :return: Lista de registros de execução ordenados cronologicamente.
        """
        #Verificar se as datas são válidas
        if data_inicio > data_fim:
            raise ValueError("A data de início não pode ser posterior à data de fim.")
        
        execucoes = self.execucao_repositorio.obter_execucoes_por_exercicio_e_periodo(exercicio_id, data_inicio, data_fim)
        return sorted(execucoes, key=lambda x: x.data_execucao)

    def obter_frequencia_treino(self, data_inicio: datetime, data_fim: datetime):
        """
        Calcula a frequência de treinos do usuário em um determinado período.
        :param data_inicio: Data de início do período.
        :param data_fim: Data de fim do período.
        :return: Número de treinos realizados no período.
        """
        #Verificar se as datas são válidas
        if data_inicio > data_fim:
            raise ValueError("A data de início não pode ser posterior à data de fim.")
        
        execucoes = self.execucao_repositorio.obter_execucoes_por_periodo(data_inicio, data_fim)
        return len(execucoes)
    
    def obter_volume_treino(self, data_inicio: datetime, data_fim: datetime):
        """
        Calcula o volume total de treino do usuário em um determinado período.
        :param data_inicio: Data de início do período.
        :param data_fim: Data de fim do período.
        :return: Volume total de treino (soma das cargas multiplicadas pelas repetições).
        """
        #Verificar se as datas são válidas
        if data_inicio > data_fim:
            raise ValueError("A data de início não pode ser posterior à data de fim.")
        
        execucoes = self.execucao_repositorio.obter_execucoes_por_periodo(data_inicio, data_fim)
        volume_total = sum(execucao.carga * execucao.repeticoes_realizadas for execucao in execucoes)
        return volume_total

    def comparar_avaliacoes_fisicas(self, avaliacao_id_1: str, avaliacao_id_2: str):
        """
        Compara os resultados de duas avaliações físicas diferentes.
        :param avaliacao_id_1: ID da primeira avaliação.
        :param avaliacao_id_2: ID da segunda avaliação.
        :return: Dicionário com a comparação dos resultados.
        """
        avaliacao_1 = self.avaliacao_fisica_repositorio.obter_avaliacao_por_id(avaliacao_id_1)
        avaliacao_2 = self.avaliacao_fisica_repositorio.obter_avaliacao_por_id(avaliacao_id_2)

        if not avaliacao_1 or not avaliacao_2:
            raise ValueError("Uma ou ambas as avaliações não foram encontradas.")

        comparacao = {
            "peso": (avaliacao_1.peso, avaliacao_2.peso),
            "percentual_gordura": (avaliacao_1.percentual_gordura, avaliacao_2.percentual_gordura),
            "massa_muscular": (avaliacao_1.massa_muscular, avaliacao_2.massa_muscular),
            "data_avaliacao": (avaliacao_1.data_avaliacao, avaliacao_2.data_avaliacao)
        }

        return comparacao

    def obter_exercicio_evolucao(self, exercicio_id: str, data_inicio: datetime, data_fim: datetime):
        """
        Retorna a evolução de um exercício específico em um determinado período.
        :param exercicio_id: ID do exercício.
        :param data_inicio: Data de início do período.
        :param data_fim: Data de fim do período.
        :return: Lista de registros de execução ordenados cronologicamente.
        """
        #Verificar se as datas são válidas
        if data_inicio > data_fim:
            raise ValueError("A data de início não pode ser posterior à data de fim.")
        
        execucoes = self.execucao_repositorio.obter_execucoes_por_exercicio_e_periodo(exercicio_id, data_inicio, data_fim)
        return sorted(execucoes, key=lambda x: x.data_execucao)


    def obter_resumo_progresso(self, data_inicio: datetime, data_fim: datetime):
        """
        Retorna um resumo geral do progresso do usuário, incluindo peso, percentual de gordura, massa muscular, força e frequência de treino.
        :param data_inicio: Data de início do período.
        :param data_fim: Data de fim do período.
        :return: Dicionário com o resumo do progresso.
        """
        #Verificar se as datas são válidas
        if data_inicio > data_fim:
            raise ValueError("A data de início não pode ser posterior à data de fim.")
        
        peso_evolucao = self.obter_peso_evolucao(data_inicio, data_fim)
        percentual_gordura_evolucao = self.obter_percentual_gordura_evolucao(data_inicio, data_fim)
        massa_muscular_evolucao = self.obter_massa_muscular_evolucao(data_inicio, data_fim)
        frequencia_treino = self.obter_frequencia_treino(data_inicio, data_fim)
        volume_treino = self.obter_volume_treino(data_inicio, data_fim)

        return {
            "peso_evolucao": peso_evolucao,
            "percentual_gordura_evolucao": percentual_gordura_evolucao,
            "massa_muscular_evolucao": massa_muscular_evolucao,
            "frequencia_treino": frequencia_treino,
            "volume_treino": volume_treino,
        }

    def obter_evolucao_treino_dia(self, treino_id: str):
        """Retorna a evolução do treino do dia agregando execuções por exercício."""
        relacoes_treino = self.treino_exercicio_repositorio.obter_treinos_exercicios_por_treino_id(treino_id)
        if not relacoes_treino:
            return []

        execucoes = self.execucao_repositorio.obter_execucoes_por_periodo(datetime(2000, 1, 1), datetime.now())
        evolucao = []

        for relacao in relacoes_treino:
            exercicio = self.exercicio_repositorio.obter_exercicio_por_id(relacao.exercicio_id)
            historico = [
                execucao for execucao in execucoes if execucao.treino_exercicio_id == relacao.id
            ]
            evolucao.append({
                "treino_exercicio_id": relacao.id,
                "exercicio_id": relacao.exercicio_id,
                "nome_exercicio": exercicio.nome if exercicio else None,
                "series_planejadas": relacao.series,
                "repeticoes_planejadas": relacao.repeticoes,
                "tempo_descanso": relacao.tempo_descanso,
                "historico": sorted(historico, key=lambda item: item.data_execucao),
            })

        return evolucao

    def obter_resumo_progresso(self, data_inicio: datetime, data_fim: datetime):
        """
        Retorna um resumo geral do progresso do usuário, incluindo peso, percentual de gordura, massa muscular, força e frequência de treino.
        :param data_inicio: Data de início do período.
        :param data_fim: Data de fim do período.
        :return: Dicionário com o resumo do progresso.
        """
        #Verificar se as datas são válidas
        if data_inicio > data_fim:
            raise ValueError("A data de início não pode ser posterior à data de fim.")
        
        peso_evolucao = self.obter_peso_evolucao(data_inicio, data_fim)
        percentual_gordura_evolucao = self.obter_percentual_gordura_evolucao(data_inicio, data_fim)
        massa_muscular_evolucao = self.obter_massa_muscular_evolucao(data_inicio, data_fim)
        frequencia_treino = self.obter_frequencia_treino(data_inicio, data_fim)
        volume_treino = self.obter_volume_treino(data_inicio, data_fim)

        resumo = {
            "peso_evolucao": peso_evolucao,
            "percentual_gordura_evolucao": percentual_gordura_evolucao,
            "massa_muscular_evolucao": massa_muscular_evolucao,
            "frequencia_treino": frequencia_treino,
            "volume_treino": volume_treino
        }

        return resumo

    def obter_metricas_dashboard(self, data_inicio: datetime = None, data_fim: datetime = None):
        """
        Retorna métricas gerais para o painel do usuário.
        :param data_inicio: Data de início do período.
        :param data_fim: Data de fim do período.
        :return: Dicionário com as métricas do dashboard.
        """
        #Verificar se as datas são válidas
        if data_inicio is not None and data_fim is not None and data_inicio > data_fim:
            raise ValueError("A data de início não pode ser posterior à data de fim.")

        if data_inicio is None and data_fim is None:
            return {
                "peso_atual": None,
                "percentual_gordura_atual": None,
                "massa_muscular_atual": None,
                "frequencia_treino": 0,
                "volume_treino": 0
            }

        resumo_progresso = self.obter_resumo_progresso(data_inicio, data_fim)
        
        metricas_dashboard = {
            "peso_atual": resumo_progresso["peso_evolucao"][-1] if resumo_progresso["peso_evolucao"] else None,
            "percentual_gordura_atual": resumo_progresso["percentual_gordura_evolucao"][-1] if resumo_progresso["percentual_gordura_evolucao"] else None,
            "massa_muscular_atual": resumo_progresso["massa_muscular_evolucao"][-1] if resumo_progresso["massa_muscular_evolucao"] else None,
            "frequencia_treino": resumo_progresso["frequencia_treino"],
            "volume_treino": resumo_progresso["volume_treino"]
        }

        return metricas_dashboard