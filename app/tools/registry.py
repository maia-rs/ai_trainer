from app.tools.avaliacao_fisica.atualizar_avaliacao_fisica import atualizar_avaliacao_fisica
from app.tools.avaliacao_fisica.obter_avaliacao_fisica import obter_avaliacao_fisica
from app.tools.avaliacao_fisica.obter_historico_avaliacao_fisica import obter_historico_avaliacao_fisica
from app.tools.avaliacao_fisica.registrar_avaliacao_fisica import registrar_avaliacao_fisica
from app.tools.dashboard.gerar_link_dashboard import gerar_link_dashboard
from app.tools.execucao.listar_execucoes_recentes import listar_execucoes_recentes
from app.tools.execucao.obter_historico_treino import obter_historico_treino
from app.tools.execucao.obter_ultima_execucao import obter_ultima_execucao
from app.tools.execucao.registrar_execucao_com_feedback import registrar_execucao_com_feedback
from app.tools.execucao.registrar_execucao_treino import registrar_execucao_treino
from app.tools.execucao.resumo_treino_hoje import resumo_treino_hoje
from app.tools.exercicio.buscar_informacoes_exercicio import buscar_informacoes_exercicio
from app.tools.progresso.comparar_avaliacoes_fisicas import comparar_avaliacoes_fisicas
from app.tools.progresso.obter_progresso import obter_progresso
from app.tools.progresso.obter_progresso_exercicio import obter_progresso_exercicio
from app.tools.progresso.obter_resumo_progresso import obter_resumo_progresso
from app.tools.treino.atualizar_treino import atualizar_treino
from app.tools.treino.criar_treino import criar_treino
from app.tools.treino.desativar_treino import desativar_treino
from app.tools.treino.listar_treinos_usuario import listar_treinos_usuario
from app.tools.treino.obter_treino_do_dia import obter_treino_do_dia
from app.tools.treino_exercicio.adicionar_exercicio_treino import adicionar_exercicio_treino
from app.tools.treino_exercicio.atualizar_exercicio_treino import atualizar_exercicio_treino
from app.tools.treino_exercicio.buscar_exercicio_no_treino import buscar_exercicio_no_treino
from app.tools.treino_exercicio.obter_exercicios_treino import obter_exercicios_treino
from app.tools.treino_exercicio.remover_exercicio_treino import remover_exercicio_treino
from app.tools.usuario.consultar_usuario import consultar_usuario
from app.tools.usuario.usuario_criar import criar_usuario


def get_agent_tools() -> list:
    """Retorna as tools disponiveis para o agente."""
    return [
        consultar_usuario,
        criar_usuario,
        criar_treino,
        atualizar_treino,
        desativar_treino,
        listar_treinos_usuario,
        obter_treino_do_dia,
        adicionar_exercicio_treino,
        atualizar_exercicio_treino,
        buscar_exercicio_no_treino,
        obter_exercicios_treino,
        remover_exercicio_treino,
        registrar_execucao_treino,
        registrar_execucao_com_feedback,
        resumo_treino_hoje,
        listar_execucoes_recentes,
        obter_ultima_execucao,
        obter_historico_treino,
        registrar_avaliacao_fisica,
        obter_avaliacao_fisica,
        obter_historico_avaliacao_fisica,
        atualizar_avaliacao_fisica,
        obter_progresso,
        obter_progresso_exercicio,
        obter_resumo_progresso,
        comparar_avaliacoes_fisicas,
        buscar_informacoes_exercicio,
        gerar_link_dashboard,
    ]
