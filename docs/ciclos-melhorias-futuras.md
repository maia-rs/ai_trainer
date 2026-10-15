# Melhorias Futuras — Ciclos de Treino

## 1. Janela temporal do ciclo (`data_inicio` ativa + `data_fim`)

**Ideia:** Adicionar um campo `data_fim` opcional ao model `Ciclo`, permitindo que o agente saiba o período de vigência do ciclo.

**Comportamento esperado:**
- `data_inicio` já existe no model — passa a funcionar também como "data a partir da qual o ciclo entra em vigor"
- `data_fim` seria opcional — define um prazo para o ciclo terminar, mas não bloqueia a conclusão por sessões
- `CicloService.obter_treino_do_dia` verificaria `data_inicio <= hoje` antes de usar o ciclo (ciclos futuros são ignorados)
- Se `data_fim` for definida e `hoje > data_fim`, o ciclo deixa de ser considerado ativo para o agente

**Casos de uso:**
- Usuário planeja um bloco de hipertrofia de 12 semanas (jan → mar)
- Agente começa a sugerir treinos do ciclo apenas na `data_inicio`
- Após `data_fim`, agente volta ao comportamento padrão de dia da semana

**Perguntas em aberto antes de implementar:**
- O que acontece se `data_fim` chega com sessões pendentes? Ciclo expira automaticamente ou só avisa?
- `data_fim` é calculada automaticamente (ex: `data_inicio + N semanas`) ou definida manualmente?
- Um ciclo futuro aparece para o usuário se ele perguntar, mas sem ser o "ativo do dia"?

**Impacto técnico estimado:**
- Migration: adicionar coluna `data_fim DATE NULL` na tabela `ciclos`
- `CicloRepositorio.obter_ciclo_ativo_por_usuario`: adicionar filtro `data_inicio <= hoje`
- `CicloService.obter_proxima_sessao`: verificar janela temporal antes de retornar sessão
- System prompt: instruir o agente sobre ciclos futuros agendados

---

## 2. Tool de conveniência: `criar_ciclo_com_rotacao`

**Ideia:** Tool que cria o ciclo e popula todas as sessões automaticamente a partir de uma rotação de treinos e uma duração em meses.

**Interface esperada:**
```
criar_ciclo_com_rotacao(
    usuario_id: str,
    nome: str,
    data_inicio: str,          # YYYY-MM-DD
    treino_ids: list[str],     # ex: [id_A, id_B, id_C, id_D]
    duracao_meses: int         # ex: 3
)
```

**Lógica interna:**
1. Busca `usuario.meta_semanal_dias` — já existe no model `Usuario` (default=4)
2. Calcula total de sessões: `duracao_meses × 4 semanas × meta_semanal_dias`
   - Ex: 3 meses × 4 × 4 = 48 sessões para treino 4x/semana
3. Distribui a rotação continuando de onde parou entre semanas:
   - Semana 1: A B C D (4 dias)
   - Semana 2: A B C D (começa do A novamente)
   - Se 5 dias/semana: A B C D A | B C D A B | ...
4. Chama `adicionar_sessao` internamente para cada sessão

**Por que usar `meta_semanal_dias` e não perguntar ao usuário:**
- A informação já existe e é exibida no dashboard
- Evita fricção desnecessária na conversa
- O agente pode confirmar: "Vou criar 48 sessões (4x/semana × 3 meses). Confirma?"

**Impacto técnico estimado:**
- Nova tool `app/tools/ciclo/criar_ciclo_com_rotacao.py`
- Nenhuma mudança no model ou banco
- `CicloService` ganha método `criar_ciclo_com_rotacao()`
- Registrar no `registry.py` e system prompt

---

## 3. Sessão por semana vs. sessão por treino

**Observação:** No modelo atual, sessão = uma execução de treino (não uma semana).
Exemplos:
- Treino ABCD → 4 sessões por semana
- Treino full body 3x → 3 sessões por semana

Se no futuro o produto quiser agrupar sessões por semana (ex: "semana 1 do ciclo"), 
seria necessário adicionar um campo `semana` ou `bloco` à `CicloSessao` e ajustar 
a lógica de progressão.
