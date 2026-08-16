from sqlalchemy.orm import Session

from app.models.exercicio import Exercicio
from app.repositorio.exercicio import ExercicioRepositorio
from app.schemas.exercicio import ExercicioCreate, ExercicioUpdate,ExercicioResponse

"""
O external_id deve ser único.
O exercício não pode ser removido fisicamente.
A atualização do catálogo deve ocorrer através do Pipeline de Ingestão.
Exercícios inativos não devem aparecer nas consultas do usuário.
Um exercício pode estar presente em vários treinos.
"""

class ExercicioService:

    """Classe de serviço para operações relacionadas a exercícios."""

    def __init__(self, session: Session):
        self.exercicio_repositorio = ExercicioRepositorio(session)

    def criar_exercicio(self, exercicio_create: ExercicioCreate) -> ExercicioResponse:
        """Cria um novo exercício."""
        #Verifica se o external_id já existe
        existing_exercicio = self.exercicio_repositorio.obter_exercicio_por_external_id(exercicio_create.id_externo)
        if existing_exercicio:
            raise ValueError("External ID já cadastrado.")
        dados = exercicio_create.model_dump()
        exercicio = Exercicio(**dados)

        existing_exercicio = self.exercicio_repositorio.obter_exercicio_por_external_id(exercicio.id_externo)
        if existing_exercicio:
            raise ValueError("External ID já cadastrado.")
        return ExercicioResponse.model_validate(self.exercicio_repositorio.criar_exercicio(exercicio))
    
    def obter_exercicio_por_id(self, exercicio_id: str) -> ExercicioResponse | None:
        """Obtém um exercício pelo ID."""
        #Verifica se o exercício existe
        exercicio = self.exercicio_repositorio.obter_exercicio_por_id(exercicio_id)
        if not exercicio:
            raise ValueError("Exercício não encontrado.")
        #verifica se o exercício está ativo
        if exercicio.status != "ativo":
            raise ValueError("Exercício não está ativo.")
        """Obtém um exercício pelo ID."""
        return ExercicioResponse.model_validate(exercicio)

    def obter_exercicio_por_external_id(self, external_id: str) -> ExercicioResponse | None:
        """Obtém um exercício pelo external ID."""
        #Verifica se o exercício existe
        exercicio = self.exercicio_repositorio.obter_exercicio_por_external_id(external_id)
        if not exercicio:
            raise ValueError("Exercício não encontrado.")
        #verifica se o exercício está ativo
        if exercicio.status != "ativo":
            raise ValueError("Exercício não está ativo.")
        
        return ExercicioResponse.model_validate(exercicio)
    
    def listar_exercicios(self, limite: int = 10) -> list[ExercicioResponse]:
        
        """Lista exercícios ativos."""
        return [ExercicioResponse.model_validate(exercicio) for exercicio in self.exercicio_repositorio.buscar_exercicios(limite=limite)]

    def obter_exercicios_por_treino(self, treino_id: str) -> list[ExercicioResponse]:
        """Obtém os exercícios vinculados a um treino."""
        from app.repositorio.treino_exercicio import TreinoExercicioRepositorio
        relacoes = TreinoExercicioRepositorio(self.exercicio_repositorio.session).obter_treinos_exercicios_por_treino_id(treino_id)
        exercicios = []
        for relacao in relacoes:
            exercicio = self.exercicio_repositorio.obter_exercicio_por_id(relacao.exercicio_id)
            if exercicio:
                exercicios.append(exercicio)
        return [ExercicioResponse.model_validate(exercicio) for exercicio in exercicios]

    def buscar_exercicios(self, nome: str | None = None, categoria: str | None = None, grupo_muscular: str | None = None, limite: int = 10) -> list[ExercicioResponse]:

        """Busca exercícios por critérios opcionais."""
        #Verifica se os parâmetros de busca são válidos
        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")
        #Verifica se o nome, categoria e grupo_muscular são strings válidas
        if nome is not None and not isinstance(nome, str):
            raise ValueError("O nome deve ser uma string.")
        if categoria is not None and not isinstance(categoria, str):
            raise ValueError("A categoria deve ser uma string.")
        if grupo_muscular is not None and not isinstance(grupo_muscular, str):
            raise ValueError("O grupo muscular deve ser uma string.")
        #Verifica se o limite é um inteiro válido e maior que zero:
        if not isinstance(limite, int) or limite <= 0:
            raise ValueError("O limite deve ser um inteiro maior que zero.")

        return [ExercicioResponse.model_validate(exercicio) for exercicio in self.exercicio_repositorio.buscar_exercicios(
            nome=nome,
            categoria=categoria,
            grupo_muscular=grupo_muscular,
            limite=limite,
        )]

    def search_exercicios(self, nome: str | None = None, categoria: str | None = None, grupo_muscular: str | None = None, limite: int = 10) -> list[ExercicioResponse]:
        exercicios = self.exercicio_repositorio.buscar_exercicios(
            nome=nome,
            categoria=categoria,
            grupo_muscular=grupo_muscular,
            limite=limite,
        )
        return [ExercicioResponse.model_validate(exercicio) for exercicio in exercicios]

    def atualizar_exercicio(self, exercicio_id: str, exercicio_update: ExercicioUpdate) -> ExercicioResponse | None:
        """Atualiza um exercício existente."""
        exercicio = self.exercicio_repositorio.obter_exercicio_por_id(exercicio_id)
        if not exercicio:
            return None

        for key, value in exercicio_update.model_dump(exclude_unset=True).items():
            setattr(exercicio, key, value)

        return ExercicioResponse.model_validate(self.exercicio_repositorio.atualizar_exercicio(exercicio))

    def desativar_exercicio(self, exercicio_id: str) -> ExercicioResponse | None:
        """Desativa um exercício existente."""
        exercicio = self.exercicio_repositorio.obter_exercicio_por_id(exercicio_id)
        if not exercicio:
            return None
        exercicio.status = "inativo"
        return ExercicioResponse.model_validate(self.exercicio_repositorio.atualizar_exercicio(exercicio))