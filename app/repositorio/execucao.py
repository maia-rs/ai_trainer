from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.execucao import Execucao
from app.models.treino_exercicio import TreinoExercicio



class ExecucaoRepositorio:
    """Classe de repositório para operações de banco de dados relacionadas a execuções."""

    def __init__(self, session: Session):
        self.session = session

    def criar_execucao(self, execucao: Execucao) -> Execucao:
        """Cria uma nova execução no banco de dados."""
        self.session.add(execucao)
        self.session.commit()
        self.session.refresh(execucao)
        return execucao

    def obter_execucao_por_id(self, execucao_id: str) -> Execucao | None:
        """Obtém uma execução pelo ID."""
        stmt = select(Execucao).where(Execucao.id == execucao_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def obter_execucoes_por_treino_id(self, treino_id: str) -> list[Execucao]:
        """Obtém todas as execuções de um treino."""
        stmt = select(Execucao).where(Execucao.treino_id == treino_id)
        result = self.session.execute(stmt).scalars().all()
        return result

    def obter_execucoes_por_usuario_id(self, usuario_id: str) -> list[Execucao]:
        """Obtém todas as execuções de um usuário."""
        stmt = select(Execucao).where(Execucao.usuario_id == usuario_id)
        result = self.session.execute(stmt).scalars().all()
        return result   

    def obter_ultima_execucao_por_usuario_e_exercicio(self, usuario_id: str, exercicio_id: str) -> Execucao | None:
        """Obtém a última execução de um usuário para um exercício específico."""
        stmt = select(Execucao).where(
            Execucao.usuario_id == usuario_id,
            Execucao.exercicio_id == exercicio_id
        ).order_by(Execucao.data_execucao.desc())
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def obter_historico_execucoes_por_usuario(self, usuario_id: str) -> list[Execucao]:
        """Obtém o histórico de execuções de um usuário."""
        stmt = select(Execucao).where(Execucao.usuario_id == usuario_id).order_by(Execucao.data_execucao.desc())
        result = self.session.execute(stmt).scalars().all()
        return result

    def obter_historico_execucoes_por_exercicio(self, exercicio_id: str) -> list[Execucao]:
        """Obtém o histórico de execuções de um exercício específico."""
        stmt = select(Execucao).join(TreinoExercicio, Execucao.treino_exercicio_id == TreinoExercicio.id).where(
            TreinoExercicio.exercicio_id == exercicio_id
        ).order_by(Execucao.data_execucao.desc())
        result = self.session.execute(stmt).scalars().all()
        return result

    def obter_execucoes_por_periodo(self, data_inicio, data_fim) -> list[Execucao]:
        """Obtém execuções dentro de um intervalo de datas."""
        stmt = select(Execucao).where(
            Execucao.data_execucao >= data_inicio,
            Execucao.data_execucao <= data_fim,
        ).order_by(Execucao.data_execucao.asc())
        return self.session.execute(stmt).scalars().all()

    def obter_execucoes_por_exercicio_e_periodo(self, exercicio_id: str, data_inicio, data_fim) -> list[Execucao]:
        """Obtém execuções de um exercício específico dentro de um intervalo de datas."""
        stmt = select(Execucao).join(TreinoExercicio, Execucao.treino_exercicio_id == TreinoExercicio.id).where(
            TreinoExercicio.exercicio_id == exercicio_id,
            Execucao.data_execucao >= data_inicio,
            Execucao.data_execucao <= data_fim,
        ).order_by(Execucao.data_execucao.asc())
        return self.session.execute(stmt).scalars().all()

    def obter_ultimas_execucoes(self, limite: int = 10) -> list[Execucao]:
        """Obtém as execuções mais recentes."""
        stmt = select(Execucao).order_by(Execucao.data_execucao.desc()).limit(limite)
        return self.session.execute(stmt).scalars().all()
