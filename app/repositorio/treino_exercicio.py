from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.treino_exercicio import TreinoExercicio 



class TreinoExercicioRepositorio:
    """Classe de repositório para operações de banco de dados relacionadas a treinos e exercícios."""

    def __init__(self, session: Session):
        self.session = session

    def criar_treino_exercicio(self, treino_exercicio: TreinoExercicio) -> TreinoExercicio:
        """Cria um novo treino_exercicio no banco de dados."""
        self.session.add(treino_exercicio)
        self.session.commit()
        self.session.refresh(treino_exercicio)
        return treino_exercicio

    def obter_treino_exercicio_por_id(self, treino_exercicio_id: str) -> TreinoExercicio | None:
        """Obtém um treino_exercicio pelo ID."""
        stmt = select(TreinoExercicio).where(TreinoExercicio.id == treino_exercicio_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def obter_treinos_exercicios_por_treino_id(self, treino_id: str) -> list[TreinoExercicio]:
        """Obtém todos os treinos_exercicios de um treino."""
        stmt = select(TreinoExercicio).where(TreinoExercicio.treino_id == treino_id)
        result = self.session.execute(stmt).scalars().all()
        return result

    def obter_treino_exercicio_por_treino_e_exercicio(self, treino_id: str, exercicio_id: str) -> TreinoExercicio | None:
        """Obtém um treino_exercicio pelo ID do treino e do exercício."""
        stmt = select(TreinoExercicio).where(
            TreinoExercicio.treino_id == treino_id,
            TreinoExercicio.exercicio_id == exercicio_id
        )
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def atualizar_treino_exercicio(self, treino_exercicio: TreinoExercicio) -> TreinoExercicio:
        """Atualiza um treino_exercicio existente no banco de dados."""
        self.session.commit()
        self.session.refresh(treino_exercicio)
        return treino_exercicio

    def deletar_treino_exercicio(self, treino_exercicio: TreinoExercicio) -> None:
        """Deleta um treino_exercicio do banco de dados."""
        self.session.delete(treino_exercicio)
        self.session.commit()