from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ciclo import Ciclo, StatusCiclo
from app.models.ciclo_sessao import CicloSessao, StatusCicloSessao
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

    def desativar_ciclo(self, ciclo_id: str) -> CicloResponse:
        """Marca um ciclo como pausado, liberando o usuário para criar um novo ciclo ativo."""
        ciclo = self.ciclo_repo.obter_ciclo_por_id(ciclo_id)
        if not ciclo:
            raise ValueError("Ciclo não encontrado.")
        if ciclo.status == StatusCiclo.CONCLUIDO.value:
            raise ValueError("Ciclo já está concluído e não pode ser desativado.")
        ciclo.status = StatusCiclo.PAUSADO.value
        return CicloResponse.model_validate(self.ciclo_repo.atualizar_ciclo(ciclo))

    # ── Sessões ────────────────────────────────────────────────────────────

    def adicionar_sessao(
        self, ciclo_id: str, numero_sessao: int, treino_id: str
    ) -> CicloSessaoResponse:
        """Adiciona uma sessão ao ciclo com status inicial 'aguardando'."""
        ciclo = self.ciclo_repo.obter_ciclo_por_id(ciclo_id)
        if not ciclo:
            raise ValueError("Ciclo não encontrado.")

        treino = self.treino_service.obter_treino_por_id(treino_id)
        if not treino:
            raise ValueError("Treino não encontrado.")

        existente = self.sessao_repo.obter_sessao_por_numero(ciclo_id, numero_sessao)
        if existente:
            raise ValueError(f"Sessão {numero_sessao} já existe no ciclo.")

        sessao = CicloSessao(
            ciclo_id=ciclo_id,
            numero_sessao=numero_sessao,
            treino_id=treino_id,
            status=StatusCicloSessao.AGUARDANDO.value,
        )
        try:
            return CicloSessaoResponse.model_validate(self.sessao_repo.criar_sessao(sessao))
        except IntegrityError:
            self.session.rollback()
            raise ValueError(f"Sessão {numero_sessao} já existe no ciclo (violação de unicidade).")

    def iniciar_sessao(self, ciclo_sessao_id: str) -> CicloSessaoResponse:
        """Muda status da sessão para 'em_execucao' quando o usuário começa o treino."""
        sessao = self.sessao_repo.obter_sessao_por_id(ciclo_sessao_id)
        if not sessao:
            raise ValueError("Sessão não encontrada.")
        if sessao.status == StatusCicloSessao.CONCLUIDA.value:
            raise ValueError("Sessão já foi concluída.")
        if sessao.status == StatusCicloSessao.EM_EXECUCAO.value:
            return CicloSessaoResponse.model_validate(sessao)  # idempotente

        sessao.status = StatusCicloSessao.EM_EXECUCAO.value
        sessao.data_inicio_execucao = datetime.now(timezone.utc)
        return CicloSessaoResponse.model_validate(self.sessao_repo.atualizar_sessao(sessao))

    def obter_proxima_sessao(self, usuario_id: str) -> dict | None:
        """Retorna a próxima sessão do ciclo ativo.

        Prioriza sessão com status='em_execucao' (retomada).
        Se não houver, busca a próxima 'aguardando' e a inicia automaticamente.
        Se todas concluídas, fecha o ciclo e retorna None.
        """
        ciclo = self.ciclo_repo.obter_ciclo_ativo_por_usuario(usuario_id)
        if not ciclo:
            return None

        # Verifica se há sessão em execução (retomada de sessão em aberto)
        sessao = self.sessao_repo.obter_sessao_em_execucao(ciclo.id)

        if not sessao:
            # Busca próxima aguardando e a inicia
            sessao = self.sessao_repo.obter_proxima_sessao(ciclo.id)
            if not sessao:
                # Todas concluídas — fecha o ciclo
                ciclo.status = StatusCiclo.CONCLUIDO.value
                self.ciclo_repo.atualizar_ciclo(ciclo)
                return None
            # Muda para em_execucao
            sessao.status = StatusCicloSessao.EM_EXECUCAO.value
            sessao.data_inicio_execucao = datetime.now(timezone.utc)
            self.sessao_repo.atualizar_sessao(sessao)

        treino = self.treino_service.obter_treino_por_id(sessao.treino_id)
        return {
            "ciclo_sessao_id": sessao.id,
            "numero_sessao": sessao.numero_sessao,
            "treino_id": sessao.treino_id,
            "treino_nome": treino.nome if treino else None,
            "treino_descricao": treino.descricao if treino else None,
            "status": sessao.status,
            "data_inicio_execucao": sessao.data_inicio_execucao.isoformat() if sessao.data_inicio_execucao else None,
        }

    def concluir_sessao(self, ciclo_sessao_id: str) -> CicloSessaoResponse:
        """Marca uma sessão como concluída."""
        sessao = self.sessao_repo.obter_sessao_por_id(ciclo_sessao_id)
        if not sessao:
            raise ValueError("Sessão não encontrada.")
        if sessao.status == StatusCicloSessao.CONCLUIDA.value:
            raise ValueError("Sessão já foi concluída.")

        sessao.status = StatusCicloSessao.CONCLUIDA.value
        sessao.data_conclusao = datetime.now(timezone.utc)
        resultado = CicloSessaoResponse.model_validate(self.sessao_repo.atualizar_sessao(sessao))

        # Verifica se era a última sessão pendente (aguardando ou em_execucao)
        proxima_aguardando = self.sessao_repo.obter_proxima_sessao(sessao.ciclo_id)
        em_execucao = self.sessao_repo.obter_sessao_em_execucao(sessao.ciclo_id)
        if proxima_aguardando is None and em_execucao is None:
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
        concluidas = sum(1 for s in sessoes if s.status == StatusCicloSessao.CONCLUIDA.value)
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
        """Cria um ciclo e popula as sessões automaticamente usando rotação de treinos."""
        if not treino_ids:
            raise ValueError("É necessário informar ao menos um treino para a rotação.")
        if duracao_meses < 1:
            raise ValueError("Duração deve ser de pelo menos 1 mês.")

        for tid in treino_ids:
            if not self.treino_service.obter_treino_por_id(tid):
                raise ValueError(f"Treino '{tid}' não encontrado.")

        usuario = self.usuario_service.obter_usuario_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")
        if usuario.status != "ativo":
            raise ValueError("Usuário não está ativo.")

        dias_por_semana = usuario.meta_semanal_dias or 4
        semanas = duracao_meses * 4
        total_sessoes = semanas * dias_por_semana

        ciclo = self.criar_ciclo(usuario_id, nome, data_inicio)

        n_treinos = len(treino_ids)
        for i in range(total_sessoes):
            treino_id = treino_ids[i % n_treinos]
            self.adicionar_sessao(ciclo.id, i + 1, treino_id)

        return {
            "ciclo": ciclo.model_dump(),
            "total_sessoes": total_sessoes,
            "dias_por_semana": dias_por_semana,
            "rotacao": list(treino_ids),
        }

    # ── Integração com treino do dia ───────────────────────────────────────

    def obter_treino_do_dia(self, usuario_id: str) -> dict:
        """Retorna o treino do dia priorizando o ciclo ativo.

        Se há sessão 'em_execucao' de uma data anterior, sinaliza sessão em aberto.
        Se há ciclo ativo → {"fonte": "ciclo", ...}
        Caso contrário → {"fonte": "dia_semana", ...}
        """
        ciclo = self.ciclo_repo.obter_ciclo_ativo_por_usuario(usuario_id)
        if not ciclo:
            treino_dia = self.treino_service.obter_treino_do_dia_por_usuario(usuario_id)
            return {"fonte": "dia_semana", "treino": treino_dia}

        # Verifica sessão em execução que pode ser de dia anterior
        sessao_em_aberto = self.sessao_repo.obter_sessao_em_execucao(ciclo.id)
        hoje = datetime.now(timezone.utc).date()

        if sessao_em_aberto:
            data_inicio = sessao_em_aberto.data_inicio_execucao
            data_inicio_date = data_inicio.astimezone(timezone.utc).date() if data_inicio else None

            if data_inicio_date and data_inicio_date < hoje:
                # Sessão em aberto de dia anterior — alerta
                treino = self.treino_service.obter_treino_por_id(sessao_em_aberto.treino_id)
                return {
                    "fonte": "ciclo",
                    "sessao_em_aberto": True,
                    "ciclo_sessao_id": sessao_em_aberto.id,
                    "numero_sessao": sessao_em_aberto.numero_sessao,
                    "data_inicio_execucao": data_inicio.isoformat() if data_inicio else None,
                    "treino": {
                        "id": sessao_em_aberto.treino_id,
                        "nome": treino.nome if treino else None,
                        "descricao": treino.descricao if treino else None,
                    },
                }

        # Fluxo normal: pega próxima sessão (em_execucao de hoje ou aguardando)
        proxima = self.obter_proxima_sessao(usuario_id)
        if proxima:
            return {
                "fonte": "ciclo",
                "sessao_em_aberto": False,
                "ciclo_sessao_id": proxima["ciclo_sessao_id"],
                "treino": {
                    "id": proxima["treino_id"],
                    "nome": proxima["treino_nome"],
                    "descricao": proxima["treino_descricao"],
                },
            }

        treino_dia = self.treino_service.obter_treino_do_dia_por_usuario(usuario_id)
        return {"fonte": "dia_semana", "treino": treino_dia}
