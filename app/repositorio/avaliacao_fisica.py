from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.avaliacao_fisica import AvaliacaoFisica

"""create
get_by_id
get_by_user_id
get_latest_by_user_id
get_history_by_user
update"""

class AvaliacaoFisicaRepositorio:
    """Classe de repositório para operações de banco de dados relacionadas a avaliações físicas."""

    def __init__(self, session: Session):
        self.session = session

    def criar_avaliacao_fisica(self, avaliacao_fisica: AvaliacaoFisica) -> AvaliacaoFisica:
        """Cria uma nova avaliação física no banco de dados."""
        self.session.add(avaliacao_fisica)
        self.session.commit()
        self.session.refresh(avaliacao_fisica)
        return avaliacao_fisica

    def obter_avaliacao_fisica_por_id(self, avaliacao_fisica_id: str) -> AvaliacaoFisica | None:
        """Obtém uma avaliação física pelo ID."""
        stmt = select(AvaliacaoFisica).where(AvaliacaoFisica.id == avaliacao_fisica_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def obter_avaliacoes_fisicas_por_usuario_id(self, usuario_id: str) -> list[AvaliacaoFisica]:
        """Obtém todas as avaliações físicas de um usuário."""
        stmt = select(AvaliacaoFisica).where(AvaliacaoFisica.usuario_id == usuario_id)
        result = self.session.execute(stmt).scalars().all()
        return result

    def obter_ultima_avaliacao_fisica_por_usuario_id(self, usuario_id: str) -> AvaliacaoFisica | None:
        """Obtém a última avaliação física de um usuário."""
        stmt = select(AvaliacaoFisica).where(AvaliacaoFisica.usuario_id == usuario_id).order_by(AvaliacaoFisica.data_avaliacao.desc())
        result = self.session.execute(stmt).scalars().first()
        return result

    def obter_avaliacoes_por_periodo(self, data_inicio, data_fim) -> list[AvaliacaoFisica]:
        """Obtém avaliações físicas dentro de um intervalo de datas."""
        stmt = select(AvaliacaoFisica).where(
            AvaliacaoFisica.data_avaliacao >= data_inicio,
            AvaliacaoFisica.data_avaliacao <= data_fim,
        ).order_by(AvaliacaoFisica.data_avaliacao.asc())
        return self.session.execute(stmt).scalars().all()

    def atualizar_avaliacao_fisica(self, avaliacao_fisica: AvaliacaoFisica) -> AvaliacaoFisica:
        """Atualiza uma avaliação física existente no banco de dados."""
        self.session.commit()
        self.session.refresh(avaliacao_fisica)
        return avaliacao_fisica

    def deletar_avaliacao_fisica(self, avaliacao_fisica_id: str) -> bool:
        """Deleta uma avaliação física pelo ID."""
        avaliacao = self.obter_avaliacao_fisica_por_id(avaliacao_fisica_id)
        if not avaliacao:
            return False
        self.session.delete(avaliacao)
        self.session.commit()
        return True

    # Aliases para compatibilidade com serviços existentes.
    def criar_avaliacao(self, avaliacao_fisica: AvaliacaoFisica) -> AvaliacaoFisica:
        return self.criar_avaliacao_fisica(avaliacao_fisica)

    def obter_avaliacao_por_id(self, avaliacao_fisica_id: str) -> AvaliacaoFisica | None:
        return self.obter_avaliacao_fisica_por_id(avaliacao_fisica_id)

    def listar_avaliacoes_por_usuario(self, usuario_id: str) -> list[AvaliacaoFisica]:
        return self.obter_avaliacoes_fisicas_por_usuario_id(usuario_id)

    def obter_ultima_avaliacao_por_usuario(self, usuario_id: str) -> AvaliacaoFisica | None:
        return self.obter_ultima_avaliacao_fisica_por_usuario_id(usuario_id)

    def atualizar_avaliacao(self, avaliacao_fisica: AvaliacaoFisica) -> AvaliacaoFisica:
        return self.atualizar_avaliacao_fisica(avaliacao_fisica)

    def deletar_avaliacao(self, avaliacao_fisica_id: str) -> bool:
        return self.deletar_avaliacao_fisica(avaliacao_fisica_id)