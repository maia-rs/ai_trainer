from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ciclo import Ciclo, StatusCiclo
from app.models.ciclo_sessao import CicloSessao
from app.repositorio.ciclo import CicloRepositorio
from app.repositorio.ciclo_sessao import CicloSessaoRepositorio
from app.schemas.ciclo import CicloResponse, CicloSessaoResponse
from app.service.treino_service import TreinoService
from app.service.usuario_service import UsuarioService


class CicloService:
    """Serviço de negócio para ciclos de treino."""

    def __init__(self, session: Session):
        self.session = session
        self.ciclo_repo = CicloRepositorio(session)
        self.sessao_repo = CicloSessaoRepositorio(session)
        self.usuario_service = UsuarioService(session)
        self.treino_service = TreinoService(session)

    # ── Ciclo ──────────────────────────────────────────────────────────────

    def criar_ciclo(self, usuario_id: str, nome: str, data_inicio: date) -> CicloResponse:
        """Cria um novo ciclo de treino para o usuário."""
        usuario = self.usuario_service.obter_usuario_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")
        if usuario.status != "ativo":
            raise ValueError("Usuário não está ativo.")

        existente = self.ciclo_repo.obter_ciclo_ativo_por_usuario(usuario_id)
        if existente:
            raise ValueError("Já existe um ciclo ativo para este usuário.")

        ciclo = Ciclo(
            usuario_id=usuario_id,
            nome=nome,
            data_inicio=data_inicio,
            status=StatusCiclo.ATIVO.value,
        )
        return CicloResponse.model_validate(self.ciclo_repo.criar_ciclo(ciclo))

    def obter_ciclo_ativo(self, usuario_id: str) -> CicloResponse | None:
        """Retorna o ciclo ativo do usuário, ou None."""
        ciclo = self.ciclo_repo.obter_ciclo_ativo_por_usuario(usuario_id)
        return CicloResponse.model_validate(ciclo) if ciclo else None

    def listar_ciclos_por_usuario(self, usuario_id: str) -> list[CicloResponse]:
        """Lista todos os ciclos do usuário ordenados por data_inicio decrescente."""
        ciclos = self.ciclo_repo.listar_ciclos_por_usuario(usuario_id)
        return [CicloResponse.model_validate(c) for c in ciclos]

    # ── Sessões ────────────────────────────────────────────────────────────

    def adicionar_sessao(
        self, ciclo_id: str, numero_sessao: int, treino_id: str
    ) -> CicloSessaoResponse:
        """Adiciona uma sessão ao ciclo."""
        ciclo = self.ciclo_repo.obter_ciclo_por_id(ciclo_id)
        if not ciclo:
            raise ValueError("Ciclo não encontrado.")

        treino = self.treino_service.obter_treino_por_id(treino_id)
        if not treino:
            raise ValueError("Treino não encontrado.")

        # Verifica duplicata antes de tentar INSERT para melhor mensagem de erro
        existente = self.sessao_repo.obter_sessao_por_numero(ciclo_id, numero_sessao)
        if existente:
            raise ValueError(
                f"Sessão {numero_sessao} já existe no ciclo."
            )

        sessao = CicloSessao(
            ciclo_id=ciclo_id,
            numero_sessao=numero_sessao,
            treino_id=treino_id,
        )
        try:
            return CicloSessaoResponse.model_validate(self.sessao_repo.criar_sessao(sessao))
        except IntegrityError:
            self.session.rollback()
            raise ValueError(
                f"Sessão {numero_sessao} já existe no ciclo (violação de unicidade)."
            )

    def obter_proxima_sessao(self, usuario_id: str) -> dict | None:
        """Retorna a próxima sessão pendente do ciclo ativo do usuário.

        Se todas as sessões estiverem concluídas, marca o ciclo como concluído e retorna None.
        """
        ciclo = self.ciclo_repo.obter_ciclo_ativo_por_usuario(usuario_id)
        if not ciclo:
            return None

        sessao = self.sessao_repo.obter_proxima_sessao(ciclo.id)
        if not sessao:
            # Todas as sessões concluídas — fecha o ciclo
            ciclo.status = StatusCiclo.CONCLUIDO.value
            self.ciclo_repo.atualizar_ciclo(ciclo)
            return None

        treino = self.treino_service.obter_treino_por_id(sessao.treino_id)
        return {
            "ciclo_sessao_id": sessao.id,
            "numero_sessao": sessao.numero_sessao,
            "treino_id": sessao.treino_id,
            "treino_nome": treino.nome if treino else None,
            "treino_descricao": treino.descricao if treino else None,
        }

    def concluir_sessao(self, ciclo_sessao_id: str) -> CicloSessaoResponse:
        """Marca uma sessão como concluída.

        Se for a última sessão pendente, marca o ciclo como concluído também.
        """
        sessao = self.sessao_repo.obter_sessao_por_id(ciclo_sessao_id)
        if not sessao:
            raise ValueError("Sessão não encontrada.")
        if sessao.concluido:
            raise ValueError("Sessão já foi concluída.")

        sessao.concluido = True
        sessao.data_conclusao = datetime.now(timezone.utc)
        resultado = CicloSessaoResponse.model_validate(self.sessao_repo.atualizar_sessao(sessao))

        # Verifica se era a última sessão pendente
        proxima = self.sessao_repo.obter_proxima_sessao(sessao.ciclo_id)
        if proxima is None:
            ciclo = self.ciclo_repo.obter_ciclo_por_id(sessao.ciclo_id)
            if ciclo and ciclo.status == StatusCiclo.ATIVO.value:
                ciclo.status = StatusCiclo.CONCLUIDO.value
                self.ciclo_repo.atualizar_ciclo(ciclo)

        return resultado

    def obter_progresso_ciclo(self, ciclo_id: str) -> dict:
        """Retorna métricas de progresso do ciclo."""
        ciclo = self.ciclo_repo.obter_ciclo_por_id(ciclo_id)
        if not ciclo:
            raise ValueError("Ciclo não encontrado.")
        sessoes = self.sessao_repo.listar_sessoes_por_ciclo(ciclo_id)
        total = len(sessoes)
        concluidas = sum(1 for s in sessoes if s.concluido)
        percentual = round((concluidas / total * 100), 1) if total > 0 else 0.0
        return {
            "sessoes_concluidas": concluidas,
            "total_sessoes": total,
            "percentual_conclusao": percentual,
        }

    def criar_ciclo_com_rotacao(
        self,
        usuario_id: str,
        nome: str,
        data_inicio: date,
        treino_ids: list[str],
        duracao_meses: int,
    ) -> dict:
        """Cria um ciclo e popula as sessões automaticamente usando rotação de treinos.

        Usa `usuario.meta_semanal_dias` para calcular o total de sessões.
        A rotação continua de onde parou entre semanas — ex: ABCD → ABCD → ...

        Returns dict com ciclo criado e total de sessões geradas.
        """
        if not treino_ids:
            raise ValueError("É necessário informar ao menos um treino para a rotação.")
        if duracao_meses < 1:
            raise ValueError("Duração deve ser de pelo menos 1 mês.")

        # Valida todos os treinos antes de criar o ciclo
        for tid in treino_ids:
            if not self.treino_service.obter_treino_por_id(tid):
                raise ValueError(f"Treino '{tid}' não encontrado.")

        # Lê meta_semanal_dias do usuário
        usuario = self.usuario_service.obter_usuario_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")
        if usuario.status != "ativo":
            raise ValueError("Usuário não está ativo.")

        dias_por_semana = usuario.meta_semanal_dias or 4
        semanas = duracao_meses * 4
        total_sessoes = semanas * dias_por_semana

        # Cria o ciclo
        ciclo = self.criar_ciclo(usuario_id, nome, data_inicio)

        # Popula sessões com rotação contínua
        n_treinos = len(treino_ids)
        for i in range(total_sessoes):
            treino_id = treino_ids[i % n_treinos]
            self.adicionar_sessao(ciclo.id, i + 1, treino_id)

        return {
            "ciclo": ciclo.model_dump(),
            "total_sessoes": total_sessoes,
            "dias_por_semana": dias_por_semana,
            "rotacao": [t for t in treino_ids],
        }

    # ── Integração com treino do dia ───────────────────────────────────────

    def obter_treino_do_dia(self, usuario_id: str) -> dict:
        """Retorna o treino do dia priorizando o ciclo ativo.

        - Se há ciclo ativo com sessão pendente → {"fonte": "ciclo", ...}
        - Caso contrário → delega para TreinoService → {"fonte": "dia_semana", ...}
        """
        proxima = self.obter_proxima_sessao(usuario_id)
        if proxima:
            treino = self.treino_service.obter_treino_por_id(proxima["treino_id"])
            return {
                "fonte": "ciclo",
                "ciclo_sessao_id": proxima["ciclo_sessao_id"],
                "treino": {
                    "id": proxima["treino_id"],
                    "nome": proxima["treino_nome"],
                    "descricao": proxima["treino_descricao"],
                },
            }

        treino_dia = self.treino_service.obter_treino_do_dia_por_usuario(usuario_id)
        return {
            "fonte": "dia_semana",
            "treino": treino_dia,
        }
