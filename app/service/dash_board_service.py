from app.core.database import get_db
from app.service.treino_exercicio import TreinoExercicioService
from app.service.exercicio_service import ExercicioService
from app.service.execucao_service import ExecucaoService
from app.service.progresso_service import ProgressoService
from app.service.avaliacao_service import AvaliacaoService
from sqlalchemy.orm import Session
from datetime import datetime

"""

get_dashboard() - Retornar todos os dados necessários para carregar o Dashboard inicial.
obter_treino_do_dia() - Retornar o treino programado para o dia.
obter_resumo_progresso() - Retornar um resumo geral da evolução do usuário.
obter_metricas_fisicas() - Retornar indicadores provenientes das avaliações físicas.
obter_evolucao_treino_dia() - Retornar a evolução do treino do dia, incluindo carga, repetições, séries, tempo de execução e descanso.
obter_atividades_recentes() - Retornar as últimas execuções registradas pelo usuário.
obter_dados_grafico() - Preparar os dados utilizados pelos gráficos do Dashboard.


Os dados apresentados devem refletir o estado mais recente da aplicação.
Caso não existam registros suficientes, retornar informações vazias de forma consistente.
O Dashboard não realiza cálculos de evolução; essa responsabilidade pertence ao ProgressService.

"""

class DashBoardService:
    def __init__(self, db: Session = get_db()):
        self.db = db
        self.treino_exercicio_service = TreinoExercicioService(db)
        self.exercicio_service = ExercicioService(db)
        self.execucao_service = ExecucaoService(db)
        self.progresso_service = ProgressoService(db)
        self.avaliacao_service = AvaliacaoService(db)

    def obter_dashboard(self):
        """
        Retorna todos os dados necessários para carregar o Dashboard inicial.
        """
        # Implementação do método para retornar os dados do dashboard
        pass

    def obter_treino_do_dia(self):
        """
        Retorna o treino programado para o dia.
        """
        #Verificar dia da semana e retornar o treino correspondente
        treino_do_dia = self.treino_exercicio_service.obter_treino_por_dia(datetime.now().weekday())
        return treino_do_dia

    def obter_resumo_progresso_geral(self):
        """
        Retorna um resumo geral da evolução do usuário.
        """
        return self.progresso_service.obter_metricas_dashboard()

    def obter_metricas_fisicas(self):
        """
        Retorna indicadores provenientes das avaliações físicas.
        """
        return self.progresso_service.obter_metricas_dashboard()

    def obter_evolucao_treino_dia(self):
        """
        Retorna a evolução do treino do dia, incluindo carga, repetições, séries, tempo de execução e descanso.
        """
        # Obter dia da semana atual
        dia_atual = datetime.now().weekday()
        # Obter treino do dia
        treino_do_dia = self.treino_exercicio_service.obter_treino_por_dia(dia_atual)
        if not treino_do_dia:
            return {"mensagem": "Nenhum treino programado para hoje."}
        #Obter exercicios do treino do dia
        exercicios_treino = self.exercicio_service.obter_exercicios_por_treino(treino_do_dia.id)
        if not exercicios_treino:
            return {"mensagem": "Nenhum exercício encontrado para o treino do dia."}
        evolucao_treino_dia = self.progresso_service.obter_evolucao_treino_dia(treino_do_dia.id)
        return evolucao_treino_dia

    def obter_atividades_recentes(self):
        """
        Retorna as últimas execuções registradas pelo usuário.
        """
        atividades_recentes = self.execucao_service.obter_ultimas_execucoes()
        return atividades_recentes

    def obter_dados_grafico(self):
        """
        Prepara os dados utilizados pelos gráficos do Dashboard.
        """
        # Implementação do método para preparar os dados dos gráficos
        pass