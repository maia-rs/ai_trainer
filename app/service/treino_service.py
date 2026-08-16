from app.schemas.treino import TreinoCreate, TreinoUpdate,TreinoResponse
from app.repositorio.treino import TreinoRepositorio
from app.models.treino import Treino, StatusTreino
from app.service.usuario_service import UsuarioService
from sqlalchemy.orm import Session


class TreinoService:
    """Classe de serviço para operações relacionadas a treinos."""

    def __init__(self, session: Session):
        self.session = session
        self.treino_repositorio = TreinoRepositorio(session)
        self.usuario_service = UsuarioService(session)

    def criar_treino(self, treino_create: TreinoCreate) -> TreinoResponse:
        #Verifica se o usuário existe
        usuario = self.usuario_service.obter_usuario_por_id(treino_create.usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")
        #Verifica se o usuário está ativo
        if usuario.status != "ativo":
            raise ValueError("Usuário não está ativo.")
        """Cria um novo treino."""
        treino = Treino(**treino_create.model_dump())
        return TreinoResponse.model_validate(self.treino_repositorio.criar_treino(treino))

    def obter_treino_por_id(self, treino_id: str) -> TreinoResponse | None:
        """Obtém um treino pelo ID."""
        treino = self.treino_repositorio.obter_treino_por_id(treino_id)
        return TreinoResponse.model_validate(treino) if treino else None

    def listar_treinos_por_usuario(self, usuario_id: str) -> list[TreinoResponse]:
        """Lista todos os treinos de um usuário."""
        treinos = self.treino_repositorio.obter_treinos_por_usuario(usuario_id)
        return [TreinoResponse.model_validate(treino) for treino in treinos]

    def atualizar_treino(self, treino_id: str, treino_update: TreinoUpdate) -> TreinoResponse | None:
        """Atualiza um treino existente."""
        treino = self.treino_repositorio.obter_treino_por_id(treino_id)
        if not treino:
            return None

        for key, value in treino_update.model_dump(exclude_unset=True).items():
            setattr(treino, key, value)

        return TreinoResponse.model_validate(self.treino_repositorio.atualizar_treino(treino))

    def desativar_treino(self, treino_id: str) -> TreinoResponse | None:
        """Desativa um treino existente."""
        treino = self.treino_repositorio.obter_treino_por_id(treino_id)
        if not treino:
            return None
        treino.status = StatusTreino.INATIVO.value
        return TreinoResponse.model_validate(self.treino_repositorio.atualizar_treino(treino))

    def duplicar_treino(self, treino_id: str) -> TreinoResponse | None:
        """Duplica um treino existente."""
        treino = self.treino_repositorio.obter_treino_por_id(treino_id)
        if not treino:
            return None

        novo_treino = Treino(
            usuario_id=treino.usuario_id,
            nome=treino.nome + " (Cópia)",
            descricao=treino.descricao,
            dia_da_semana=treino.dia_da_semana,
            status=StatusTreino.ATIVO.value,
        )
        return TreinoResponse.model_validate(self.treino_repositorio.criar_treino(novo_treino))