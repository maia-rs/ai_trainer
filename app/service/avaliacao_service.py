from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.avaliacao_fisica import AvaliacaoFisica
from app.repositorio.avaliacao_fisica import AvaliacaoFisicaRepositorio
from app.schemas.avaliacao_fisica import (
    AvaliacaoFisicaCreate,
    AvaliacaoFisicaResponse,
    AvaliacaoFisicaUpdate,
)
from app.service.usuario_service import UsuarioService


class AvaliacaoService:
    """Classe de serviço para operações relacionadas a avaliações físicas."""

    def __init__(self, session: Session):
        self.session = session
        self.avaliacao_repositorio = AvaliacaoFisicaRepositorio(session)
        self.usuario_service = UsuarioService(session)

    def criar_avaliacao(self, avaliacao_create: AvaliacaoFisicaCreate) -> AvaliacaoFisicaResponse:
        """Cria uma nova avaliação física."""
        usuario = self.usuario_service.obter_usuario_por_id(avaliacao_create.usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")

        lista_campos = [
            "peso",
            "altura",
            "percentual_gordura",
            "massa_gorda",
            "massa_muscular",
            "imc",
            "gordura_visceral",
            "agua_corporal",
            "taxa_metabolica_basal",
        ]
        for campo in lista_campos:
            valor = getattr(avaliacao_create, campo)
            if valor is not None and valor < 0:
                raise ValueError(f"O valor de {campo} deve ser maior ou igual a zero.")

        data_avaliacao = avaliacao_create.data_avaliacao
        if data_avaliacao.tzinfo is None:
            data_avaliacao = data_avaliacao.replace(tzinfo=timezone.utc)
        else:
            data_avaliacao = data_avaliacao.astimezone(timezone.utc)
        if data_avaliacao > datetime.now(timezone.utc):
            raise ValueError("A data da avaliação não pode ser futura.")

        avaliacao = AvaliacaoFisica(**avaliacao_create.model_dump())
        criada = self.avaliacao_repositorio.criar_avaliacao_fisica(avaliacao)
        return AvaliacaoFisicaResponse.model_validate(criada)

    def obter_avaliacao_por_id(self, avaliacao_id: str) -> AvaliacaoFisicaResponse | None:
        """Obtém uma avaliação física pelo ID."""
        avaliacao = self.avaliacao_repositorio.obter_avaliacao_fisica_por_id(avaliacao_id)
        if not avaliacao:
            raise ValueError("Avaliação não encontrada.")

        usuario = self.usuario_service.obter_usuario_por_id(avaliacao.usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")

        return AvaliacaoFisicaResponse.model_validate(avaliacao)

    def listar_avaliacoes_por_usuario(self, usuario_id: str) -> list[AvaliacaoFisicaResponse]:
        """Lista todas as avaliações físicas de um usuário."""
        usuario = self.usuario_service.obter_usuario_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")

        avaliacoes = self.avaliacao_repositorio.obter_avaliacoes_fisicas_por_usuario_id(usuario_id)
        if not avaliacoes:
            raise ValueError("Nenhuma avaliação encontrada para este usuário.")

        return [AvaliacaoFisicaResponse.model_validate(avaliacao) for avaliacao in avaliacoes]

    def obter_ultima_avaliacao_por_usuario(self, usuario_id: str) -> AvaliacaoFisicaResponse | None:
        """Obtém a última avaliação física de um usuário."""
        usuario = self.usuario_service.obter_usuario_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")

        ultima = self.avaliacao_repositorio.obter_ultima_avaliacao_fisica_por_usuario_id(usuario_id)
        if not ultima:
            raise ValueError("Nenhuma avaliação encontrada para este usuário.")

        return AvaliacaoFisicaResponse.model_validate(ultima)

    def atualizar_avaliacao(
        self,
        avaliacao_id: str,
        avaliacao_update: AvaliacaoFisicaUpdate,
    ) -> AvaliacaoFisicaResponse | None:
        """Atualiza uma avaliação física existente."""
        avaliacao = self.avaliacao_repositorio.obter_avaliacao_fisica_por_id(avaliacao_id)
        if not avaliacao:
            raise ValueError("Avaliação não encontrada.")

        usuario = self.usuario_service.obter_usuario_por_id(avaliacao.usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")

        lista_campos = {
            "peso",
            "altura",
            "percentual_gordura",
            "massa_gorda",
            "massa_muscular",
            "imc",
            "gordura_visceral",
            "agua_corporal",
            "taxa_metabolica_basal",
        }

        for key, value in avaliacao_update.model_dump(exclude_unset=True).items():
            if key in lista_campos and value is not None and value < 0:
                raise ValueError(f"O valor de {key} deve ser maior ou igual a zero.")
            setattr(avaliacao, key, value)

        atualizada = self.avaliacao_repositorio.atualizar_avaliacao_fisica(avaliacao)
        return AvaliacaoFisicaResponse.model_validate(atualizada)

    def deletar_avaliacao(self, avaliacao_id: str) -> bool:
        """Deleta uma avaliação física existente."""
        avaliacao = self.avaliacao_repositorio.obter_avaliacao_fisica_por_id(avaliacao_id)
        if not avaliacao:
            raise ValueError("Avaliação não encontrada.")

        usuario = self.usuario_service.obter_usuario_por_id(avaliacao.usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")

        return self.avaliacao_repositorio.deletar_avaliacao_fisica(avaliacao_id)
