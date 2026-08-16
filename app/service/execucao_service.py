from datetime import datetime, timezone

from app.schemas.execucao import (
    ExecucaoCreate,
    ExecucaoResponse,
    ExecucaoUpdate,
)
from app.repositorio.execucao import ExecucaoRepositorio
from app.models.execucao import Execucao
from app.service.usuario_service import UsuarioService
from app.service.treino_exercicio import TreinoExercicioService
from app.service.treino_service import TreinoService
from sqlalchemy.orm import Session



class ExecucaoService:

    """Classe de serviço para operações relacionadas a execuções."""

    def __init__(self, session: Session):
        self.session = session
        self.execucao_repositorio = ExecucaoRepositorio(session)
        self.usuario_service = UsuarioService(session)
        self.treino_exercicio_service = TreinoExercicioService(session)
        self.treino_service = TreinoService(session)

    def _to_response(self, execucao: Execucao) -> ExecucaoResponse:
        payload = {
            "id": execucao.id,
            "usuario_id": self._obter_usuario_id_do_treino_exercicio(execucao.treino_exercicio_id),
            "treino_exercicio_id": execucao.treino_exercicio_id,
            "data_execucao": execucao.data_execucao,
            "carga": execucao.carga,
            "series": execucao.series_realizadas,
            "repeticoes": execucao.repeticoes_realizadas,
            "tempo_descanso_real": execucao.tempo_descanso_real,
            "duracao_execucao": execucao.duracao_execucao,
            "calorias_queimadas": execucao.calorias_queimadas,
            "frequencia_cardiaca_media": execucao.frequencia_cardiaca_media,
            "observacoes": execucao.observacoes,
            "created_at": execucao.created_at,
            "updated_at": execucao.updated_at,
        }
        return ExecucaoResponse.model_validate(payload)

    def _obter_usuario_id_do_treino_exercicio(self, treino_exercicio_id: str) -> str:
        treino_exercicio = self.treino_exercicio_service.obter_treino_exercicio_por_id(treino_exercicio_id)
        if not treino_exercicio:
            raise ValueError("Exercício do treino não encontrado.")
        treino = self.treino_service.obter_treino_por_id(treino_exercicio.treino_id)
        if not treino:
            raise ValueError("Treino não encontrado.")
        return treino.usuario_id

    def registrar_execucao(self, execucao_create: ExecucaoCreate) -> ExecucaoResponse:
        """Verifica se o usuário e o exercício existem, e se o treino está ativo antes de registrar a execução."""
        # Verifica se o usuário existe
        usuario = self.usuario_service.obter_usuario_por_id(execucao_create.usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")
        if usuario.status != "ativo":
            raise ValueError("Usuário não está ativo.")

        # Verifica se o exercício do treino existe
        treino_exercicio = self.treino_exercicio_service.obter_treino_exercicio_por_id(execucao_create.treino_exercicio_id)
        if not treino_exercicio:
            raise ValueError("Exercício do treino não encontrado.")

        # Verifica se o treino está ativo
        treino = self.treino_service.obter_treino_por_id(treino_exercicio.treino_id)
        if not treino:
            raise ValueError("Treino não encontrado ou não está ativo.")
        if treino.status != "ativo":
            raise ValueError("Treino não encontrado ou não está ativo.")

        if treino.usuario_id != usuario.id:
            raise ValueError("Usuário não pertence ao treino informado.")

        # Verifica se o peso é maior ou igual a zero
        if execucao_create.carga < 0:
            raise ValueError("A carga deve ser maior ou igual a zero.")

        # Verifica se o número de séries e repetições é maior que zero
        if execucao_create.series <= 0 or execucao_create.repeticoes <= 0:
            raise ValueError("O número de séries e repetições deve ser maior que zero.")

        # Verifica se a data da execução não é futura
        data_execucao = execucao_create.data_execucao
        if data_execucao.tzinfo is None:
            data_execucao = data_execucao.replace(tzinfo=timezone.utc)
        else:
            data_execucao = data_execucao.astimezone(timezone.utc)
        if data_execucao > datetime.now(timezone.utc):
            raise ValueError("A data da execução não pode ser futura.")

        """Registra uma nova execução."""
        dados = execucao_create.model_dump()
        dados.pop("usuario_id", None)
        dados["series_realizadas"] = dados.pop("series")
        dados["repeticoes_realizadas"] = dados.pop("repeticoes")
        execucao = Execucao(**dados)
        criada = self.execucao_repositorio.criar_execucao(execucao)
        return self._to_response(criada)

    def obter_execucao_por_id(self, execucao_id: str) -> ExecucaoResponse | None:
        """Obtém uma execução pelo ID."""
        execucao = self.execucao_repositorio.obter_execucao_por_id(execucao_id)
        return self._to_response(execucao) if execucao else None

    def listar_execucoes_por_usuario(self, usuario_id: str) -> list[ExecucaoResponse]:
        """Lista todas as execuções de um usuário."""
        execucoes = self.execucao_repositorio.obter_ultimas_execucoes(limite=1000)
        filtradas = []
        for execucao in execucoes:
            try:
                execucao_usuario_id = self._obter_usuario_id_do_treino_exercicio(execucao.treino_exercicio_id)
            except ValueError:
                continue
            if execucao_usuario_id == usuario_id:
                filtradas.append(execucao)
        return [self._to_response(execucao) for execucao in filtradas]

    def obter_ultimas_execucoes(self, limite: int = 10) -> list[ExecucaoResponse]:
        """Busca as execuções mais recentes."""
        execucoes = self.execucao_repositorio.obter_ultimas_execucoes(limite=limite)
        return [self._to_response(execucao) for execucao in execucoes]

    def listar_ultimas_execucoes(self, limite: int = 10) -> list[ExecucaoResponse]:
        return self.obter_ultimas_execucoes(limite=limite)

    def atualizar_execucao(self, execucao_id: str, execucao_update: ExecucaoUpdate) -> ExecucaoResponse | None:
        """Atualiza uma execução existente."""
        execucao = self.execucao_repositorio.obter_execucao_por_id(execucao_id)
        if not execucao:
            return None

        dados_update = execucao_update.model_dump(exclude_unset=True)
        if "series" in dados_update:
            dados_update["series_realizadas"] = dados_update.pop("series")
        if "repeticoes" in dados_update:
            dados_update["repeticoes_realizadas"] = dados_update.pop("repeticoes")

        for key, value in dados_update.items():
            setattr(execucao, key, value)

        self.session.commit()
        self.session.refresh(execucao)
        return self._to_response(execucao)

    def deletar_execucao(self, execucao_id: str) -> bool:
        """Deleta uma execução existente."""
        execucao = self.execucao_repositorio.obter_execucao_por_id(execucao_id)
        if not execucao:
            return False
        self.session.delete(execucao)
        self.session.commit()
        return True