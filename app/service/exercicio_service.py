from sqlalchemy.orm import Session

from app.models.exercicio import Exercicio
from app.repositorio.exercicio import ExercicioRepositorio
from app.schemas.exercicio import ExercicioCreate, ExercicioUpdate


class ExercicioService:

    """Classe de serviço para operações relacionadas a exercícios."""

    def __init__(self, session: Session):
        self.exercicio_repositorio = ExercicioRepositorio(session)

    def criar_exercicio(self, exercicio_create: ExercicioCreate) -> Exercicio:
        """Cria um novo exercício."""
        dados = exercicio_create.model_dump()
        exercicio = Exercicio(**dados)

        existing_exercicio = self.exercicio_repositorio.obter_exercicio_por_external_id(exercicio.id_externo)
        if existing_exercicio:
            raise ValueError("External ID já cadastrado.")

        return self.exercicio_repositorio.criar_exercicio(exercicio)

    def obter_exercicio_por_id(self, exercicio_id: str) -> Exercicio | None:
        """Obtém um exercício pelo ID."""
        return self.exercicio_repositorio.obter_exercicio_por_id(exercicio_id)

    def obter_exercicio_por_external_id(self, external_id: str) -> Exercicio | None:
        """Obtém um exercício pelo external ID."""
        return self.exercicio_repositorio.obter_exercicio_por_external_id(external_id)

    def listar_exercicios(self, limite: int = 10) -> list[Exercicio]:
        """Lista exercícios ativos."""
        return self.exercicio_repositorio.buscar_exercicios(limite=limite)

    def search_exercicios(self, nome: str | None = None, categoria: str | None = None, grupo_muscular: str | None = None, limite: int = 10) -> list[Exercicio]:
        """Busca exercícios por critérios opcionais."""
        return self.exercicio_repositorio.buscar_exercicios(
            nome=nome,
            categoria=categoria,
            grupo_muscular=grupo_muscular,
            limite=limite,
        )

    def atualizar_exercicio(self, exercicio_id: str, exercicio_update: ExercicioUpdate) -> Exercicio | None:
        """Atualiza um exercício existente."""
        exercicio = self.exercicio_repositorio.obter_exercicio_por_id(exercicio_id)
        if not exercicio:
            return None

        for key, value in exercicio_update.model_dump(exclude_unset=True).items():
            setattr(exercicio, key, value)

        return self.exercicio_repositorio.atualizar_exercicio(exercicio)

    def desativar_exercicio(self, exercicio_id: str) -> Exercicio | None:
        """Desativa um exercício existente."""
        exercicio = self.exercicio_repositorio.obter_exercicio_por_id(exercicio_id)
        if not exercicio:
            return None
        exercicio.status = "inativo"
        return self.exercicio_repositorio.atualizar_exercicio(exercicio)