from sqlalchemy.orm import Session

from app.models.treino_exercicio import TreinoExercicio
from app.repositorio.treino_exercicio import TreinoExercicioRepositorio
from app.schemas.exercicio import ExercicioResponse
from app.schemas.treino import TreinoResponse
from app.schemas.treino_exercicio import (
    TreinoExercicioCreate,
    TreinoExercicioResponse,
    TreinoExercicioUpdate,
)
from app.service.exercicio_service import ExercicioService
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService


class TreinoExercicioService:
    """Classe de serviço para operações relacionadas a exercícios em treinos."""

    def __init__(self, session: Session):
        self.session = session
        self.treino_exercicio_repositorio = TreinoExercicioRepositorio(session)
        self.treino_service = TreinoService(session)
        self.exercicio_service = ExercicioService(session)
        self.usuario_service = UsuarioService(session)

    def _to_response(self, model: TreinoExercicio) -> TreinoExercicioResponse:
        payload = {
            "id": model.id,
            "treino_id": model.treino_id,
            "exercicio_id": model.exercicio_id,
            "series": model.series,
            "repeticoes": model.repeticoes,
            "descanso": model.tempo_descanso,
            "observacoes": model.observacoes,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }
        return TreinoExercicioResponse.model_validate(payload)

    def criar_treino_exercicio(self, treino_exercicio_create: TreinoExercicioCreate) -> TreinoExercicioResponse:
        # Valida treino, usuário dono do treino e exercício usando serviços.
        treino = self.treino_service.obter_treino_por_id(treino_exercicio_create.treino_id)
        if not treino:
            raise ValueError("Treino não encontrado.")
        if treino.status != "ativo":
            raise ValueError("Treino não está ativo.")

        usuario = self.usuario_service.obter_usuario_por_id(treino.usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")
        if usuario.status != "ativo":
            raise ValueError("Usuário não está ativo.")

        self.exercicio_service.obter_exercicio_por_id(treino_exercicio_create.exercicio_id)

        existente = self.treino_exercicio_repositorio.obter_treino_exercicio_por_treino_e_exercicio(
            treino_exercicio_create.treino_id,
            treino_exercicio_create.exercicio_id,
        )
        if existente:
            raise ValueError("Exercício já vinculado ao treino.")

        dados = treino_exercicio_create.model_dump()
        dados["tempo_descanso"] = dados.pop("descanso")
        treino_exercicio = TreinoExercicio(**dados)
        criado = self.treino_exercicio_repositorio.criar_treino_exercicio(treino_exercicio)
        return self._to_response(criado)

    def adicionar_exercicio(self, treino_exercicio_create: TreinoExercicioCreate) -> TreinoExercicioResponse:
        return self.criar_treino_exercicio(treino_exercicio_create)

    def obter_treino_exercicio_por_id(self, treino_exercicio_id: str) -> TreinoExercicioResponse | None:
        """Obtém um exercício de treino pelo ID."""
        treino_exercicio = self.treino_exercicio_repositorio.obter_treino_exercicio_por_id(treino_exercicio_id)
        return self._to_response(treino_exercicio) if treino_exercicio else None

    def obter_exercicio_por_id(self, treino_exercicio_id: str) -> TreinoExercicioResponse | None:
        return self.obter_treino_exercicio_por_id(treino_exercicio_id)

    def obter_treino_por_dia(self, dia_da_semana: int | str) -> TreinoResponse | None:
        """Obtém o treino ativo para um dia da semana."""
        dias = [
            "Segunda-feira",
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo",
        ]
        if isinstance(dia_da_semana, int):
            if dia_da_semana < 0 or dia_da_semana > 6:
                return None
            dia_normalizado = dias[dia_da_semana]
        else:
            entrada = str(dia_da_semana).strip().lower()
            mapa_dias = {
                "segunda": "Segunda-feira",
                "segunda-feira": "Segunda-feira",
                "terca": "Terça-feira",
                "terça": "Terça-feira",
                "terca-feira": "Terça-feira",
                "terça-feira": "Terça-feira",
                "quarta": "Quarta-feira",
                "quarta-feira": "Quarta-feira",
                "quinta": "Quinta-feira",
                "quinta-feira": "Quinta-feira",
                "sexta": "Sexta-feira",
                "sexta-feira": "Sexta-feira",
                "sabado": "Sábado",
                "sábado": "Sábado",
                "domingo": "Domingo",
            }
            dia_normalizado = mapa_dias.get(entrada)
            if not dia_normalizado:
                return None

        treino = self.treino_service.treino_repositorio.obter_treino_por_dia(dia_normalizado)
        return TreinoResponse.model_validate(treino) if treino else None

    def listar_treinos_exercicios_por_treino(self, treino_id: str) -> list[TreinoExercicioResponse]:
        """Lista todos os exercícios de um treino."""
        relacoes = self.treino_exercicio_repositorio.obter_treinos_exercicios_por_treino_id(treino_id)
        return [self._to_response(relacao) for relacao in relacoes]

    def listar_exercicios_por_treino(self, treino_id: str) -> list[TreinoExercicioResponse]:
        return self.listar_treinos_exercicios_por_treino(treino_id)

    def obter_exercicios_por_treino(self, treino_id: str) -> list[ExercicioResponse]:
        """Obtém os exercícios vinculados a um treino."""
        relacoes = self.treino_exercicio_repositorio.obter_treinos_exercicios_por_treino_id(treino_id)
        exercicios: list[ExercicioResponse] = []
        for relacao in relacoes:
            try:
                exercicio = self.exercicio_service.obter_exercicio_por_id(relacao.exercicio_id)
                if exercicio:
                    exercicios.append(exercicio)
            except ValueError:
                continue
        return exercicios

    def atualizar_treino_exercicio(
        self,
        treino_exercicio_id: str,
        treino_exercicio_update: TreinoExercicioUpdate,
    ) -> TreinoExercicioResponse | None:
        """Atualiza um exercício existente em um treino."""
        treino_exercicio = self.treino_exercicio_repositorio.obter_treino_exercicio_por_id(treino_exercicio_id)
        if not treino_exercicio:
            return None

        dados_update = treino_exercicio_update.model_dump(exclude_unset=True)
        if "descanso" in dados_update:
            dados_update["tempo_descanso"] = dados_update.pop("descanso")

        for key, value in dados_update.items():
            setattr(treino_exercicio, key, value)

        atualizado = self.treino_exercicio_repositorio.atualizar_treino_exercicio(treino_exercicio)
        return self._to_response(atualizado)

    def obter_exercicio_por_treino(self, treino_id: str, exercicio_id: str) -> TreinoExercicioResponse | None:
        """Obtém o vínculo treino-exercício por IDs."""
        relacao = self.treino_exercicio_repositorio.obter_treino_exercicio_por_treino_e_exercicio(
            treino_id,
            exercicio_id,
        )
        return self._to_response(relacao) if relacao else None

    def atualizar_exercicio(
        self,
        treino_exercicio_id: str,
        treino_exercicio_update: TreinoExercicioUpdate,
    ) -> TreinoExercicioResponse | None:
        return self.atualizar_treino_exercicio(treino_exercicio_id, treino_exercicio_update)

    def deletar_treino_exercicio(self, treino_exercicio_id: str) -> bool:
        """Remove um exercício de um treino."""
        treino_exercicio = self.treino_exercicio_repositorio.obter_treino_exercicio_por_id(treino_exercicio_id)
        if not treino_exercicio:
            return False
        self.treino_exercicio_repositorio.deletar_treino_exercicio(treino_exercicio)
        return True

    def remover_exercicio(self, treino_exercicio_id: str) -> bool:
        return self.deletar_treino_exercicio(treino_exercicio_id)
