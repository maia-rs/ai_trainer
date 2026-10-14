# Proposta — Funcionalidade de Ciclos de Treino

**Status:** Validado — aguardando spec  
**Data:** Outubro/2026  
**Autor:** AITrainer Dev

---

## Contexto e comportamento validado

O plano de treinos é rotativo: existem treinos nomeados (A, B, C, D) e cada semana tem uma sequência específica de sessões. O padrão não é "treino por dia da semana fixo" mas sim **sessões em sequência contínua**.

**Exemplo real (5 sessões/semana, 12 semanas):**
```
Semana 1:  A (seg) → B (ter) → C (qua) → D (qui) → A (sex)
Semana 2:  B (seg) → C (ter) → A (qua) → D (qui) → E (sex)
...
Semana 12: ...
```

O que determina o treino do dia **não é o dia da semana** mas sim **qual é a próxima sessão não concluída na sequência do ciclo**.

---

## Modelo de dados

```
Ciclo
├── id (uuid)
├── usuario_id (FK → usuarios)
├── nome               — ex: "Ciclo Hipertrofia Q4/2026"
├── data_inicio (date) — data de início
├── status             — ativo | concluido | pausado
└── created_at / updated_at

CicloSessao
├── id (uuid)
├── ciclo_id (FK → ciclos)
├── numero_sessao (int) — posição na sequência: 1, 2, 3, ... 60
├── treino_id (FK → treinos) — qual treino (A, B, C ou D)
├── concluido (bool, default False)
├── data_conclusao (datetime, nullable) — quando foi executada
└── created_at / updated_at
```

### Por que `numero_sessao` em vez de data?

A data é irrelevante para saber qual treino fazer. O que importa é a **posição na sequência**. Se o usuário pulou um dia ou treinou dois dias seguidos, a sequência continua correta — sempre a próxima sessão não concluída.

---

## Lógica central

```python
# Obter próxima sessão do ciclo
def obter_proxima_sessao(usuario_id):
    ciclo = obter_ciclo_ativo(usuario_id)
    return (
        SELECT * FROM ciclo_sessoes
        WHERE ciclo_id = ciclo.id AND concluido = False
        ORDER BY numero_sessao ASC
        LIMIT 1
    )
```

Quando o usuário conclui um treino, marca `concluido=True` e `data_conclusao=agora` na sessão. A próxima consulta já retorna a sessão seguinte.

---

## Montagem do ciclo (cadastro)

Para um ciclo de 12 semanas com 5 sessões/semana = 60 `CicloSessao` registradas na ordem correta:

```
Sessão 1  → Treino A
Sessão 2  → Treino B
Sessão 3  → Treino C
Sessão 4  → Treino D
Sessão 5  → Treino A
Sessão 6  → Treino B
Sessão 7  → Treino C
Sessão 8  → Treino A
Sessão 9  → Treino D
...
Sessão 60 → Treino X
```

O usuário (via agente) informa a sequência das sessões ao criar o ciclo. O agente cria os registros em ordem.

---

## Peças de implementação

### Models
- `app/models/ciclo.py`
- `app/models/ciclo_sessao.py`

### Schemas
- `app/schemas/ciclo.py` — `CicloCreate`, `CicloResponse`
- `app/schemas/ciclo_sessao.py` — `CicloSessaoCreate`, `CicloSessaoResponse`

### Repositórios
- `app/repositorio/ciclo.py`
  - `criar_ciclo`, `obter_ciclo_por_id`, `obter_ciclo_ativo_por_usuario`, `atualizar_ciclo`
- `app/repositorio/ciclo_sessao.py`
  - `criar_ciclo_sessao`, `obter_proxima_sessao`, `listar_sessoes_por_ciclo`, `concluir_sessao`

### Service
- `app/service/ciclo_service.py`
  - `criar_ciclo(usuario_id, nome, data_inicio)`
  - `adicionar_sessao(ciclo_id, numero_sessao, treino_id)`
  - `obter_ciclo_ativo(usuario_id)`
  - `obter_proxima_sessao(usuario_id)` → `CicloSessaoResponse` com treino
  - `concluir_sessao(ciclo_sessao_id)`
  - `obter_progresso_ciclo(ciclo_id)` → sessões concluídas / total

### Tools do agente
```
app/tools/ciclo/
  criar_ciclo.py              — inicia o ciclo com nome e data_inicio
  adicionar_sessao_ciclo.py   — vincula treino_id à sessão N do ciclo
  obter_proxima_sessao.py     — ← principal: retorna o treino de hoje
  concluir_sessao.py          — marca sessão como feita após o treino
  listar_ciclos_usuario.py    — histórico de ciclos
  obter_progresso_ciclo.py    — quantas sessões feitas / total
```

### Migration Alembic
- Nova migration criando `ciclos` e `ciclo_sessoes`
- `down_revision = 'c2d3e4f5a6b7'`

### System prompt (adição sugerida)
```
━━ CICLO DE TREINO ━━
- Se o usuário tiver ciclo ativo, use obter_proxima_sessao para saber
  o treino do dia — não use obter_treino_do_dia.
- Após confirmar que o treino foi concluído, chame concluir_sessao.
- Para criar ciclo: chame criar_ciclo e depois adicionar_sessao_ciclo
  para cada sessão na ordem correta.
```

---

## Alteração necessária no model Treino — `dia_da_semana` opcional

Atualmente `dia_da_semana` é **obrigatório** (`nullable=False` no model, `Field(...)` no schema). Para treinos usados em ciclos (A, B, C, D), esse campo perde o significado — o ciclo define quando cada treino é executado.

**Decisão:** tornar `dia_da_semana` **opcional** (Opção 1).

### Mudanças necessárias

**`app/models/treino.py`**
```python
# antes
dia_da_semana: Mapped[str] = mapped_column(String(20), nullable=False)

# depois
dia_da_semana: Mapped[str | None] = mapped_column(String(20), nullable=True)
```

**`app/schemas/treino.py`**
```python
# TreinoCreate — antes
dia_da_semana: str = Field(..., max_length=20)

# depois
dia_da_semana: str | None = Field(None, max_length=20)
```

**Migration Alembic** — alterar coluna `dia_da_semana` de `NOT NULL` para `NULL` (registros existentes não são afetados).

### Impacto

- Treinos existentes (com `dia_da_semana` preenchido) continuam funcionando normalmente
- `obter_treino_do_dia` filtra por `dia_da_semana` — continua funcionando para treinos com o campo preenchido
- Treinos de ciclo (A, B, C, D) são criados sem `dia_da_semana` — o ciclo cuida da sequência
- Dashboard e template já tratam campos nulos com `or "—"`

---

## O que NÃO muda

- Model `TreinoExercicio` — sem alterações
- Registro de execuções — continua igual, usa `treino_exercicio_id` normalmente
- Treinos A, B, C, D são `Treino` normais — o ciclo apenas define a sequência
- `obter_treino_do_dia` continua funcionando para usuários sem ciclo ativo

---

## Fluxo do dia a dia (após implementação)

```
Usuário: "qual é o meu treino hoje?"
Agente:  → obter_proxima_sessao(usuario_id)
         → retorna: Sessão 7 — Treino C — Costas
         → lista exercícios do Treino C

[usuário treina]

Usuário: "terminei"
Agente:  → concluir_sessao(sessao_id)
         → "Sessão 7 concluída! Próxima: Sessão 8 — Treino A — Peito"
```

---

## Próximos passos

1. ✅ Comportamento validado
2. ✅ `dia_da_semana` → opcional (decisão tomada)
3. Criar spec formal (`.kiro/specs/training-cycles/`)
4. Implementar seguindo o padrão do projeto
