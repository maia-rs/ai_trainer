from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.execucao import Execucao



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
        stmt = select(Execucao).where(Execucao.exercicio_id == exercicio_id).order_by(Execucao.data_execucao.desc())
        result = self.session.execute(stmt).scalars().all()
        return result
