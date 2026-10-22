# Backlog — AITrainer

## Alta Prioridade

### Auditoria dos dados de execução
- **Objetivo**: Revisar o banco de dados acumulado até agora — execuções, treinos, ciclos — para identificar inconsistências, duplicatas e dados mal registrados (ex: dois "lever chest press" no Treino A, exercícios adicionados durante sessão sem carga).
- **Quando**: Próxima sessão.

### GIF animado no WhatsApp
- **Problema**: A Evolution API envia o GIF como `imageMessage` mas o WhatsApp não renderiza a animação. Tentativas com `videoMessage` + `gifPlayback: true` também não funcionaram — provavelmente o Cloudflare bloqueia o request da Evolution.
- **Solução paliativa atual**: Envia o link clicável no texto para o usuário abrir no browser.
- **Solução ideal**: Converter o GIF para MP4 localmente (instalar `ffmpeg` no container) e enviar como `videoMessage` com arquivo base64, sem depender da Evolution baixar via URL. Ou usar um CDN público sem restrições (ex: Giphy, Imgur) para hospedar os GIFs.

---

## Média Prioridade

### Busca de vídeo no YouTube via DuckDuckGo
- **Ideia**: Nova tool que busca vídeos de instrução de exercícios no YouTube usando DuckDuckGo como motor de busca.
- **Interface**:
  ```
  buscar_video_exercicio(nome_exercicio: str) -> dict
  ```
  Retorna título, URL do vídeo e thumbnail.
- **Implementação sugerida**: MCP do DuckDuckGo ou `duckduckgo-search` (biblioteca Python) para buscar `"{exercicio} execução tutorial site:youtube.com"`.
- **Quando usar**: Quando o usuário pedir "mostra como fazer" ou "tem um vídeo de...".
- **Dependência**: `duckduckgo-search` ou MCP configurado.

---

## Baixa Prioridade / Futuro

### Ciclos de treino — janela temporal (`data_fim`)
- Ver detalhes em `docs/ciclos-melhorias-futuras.md`.

### Ciclos de treino — `criar_ciclo_com_rotacao` avançado
- Ver detalhes em `docs/ciclos-melhorias-futuras.md`.

---

## Considerações Futuras

### Migração do catálogo de exercícios
- **Problema**: O catálogo atual tem nomes em inglês e exercícios genéricos que às vezes não batem com o que o usuário faz na prática (ex: "triceps press" como peso corporal quando o usuário quis dizer máquina). Alguns exercícios relevantes podem estar faltando.
- **Ideia**: Avaliar catálogos alternativos ou construir um catálogo próprio com nomes em português e mapeamento para os equipamentos reais da academia.
- **Impacto**: Médio — exige migration de dados e atualização dos treinos existentes.
