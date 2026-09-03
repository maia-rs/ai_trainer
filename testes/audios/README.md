# Áudios de Teste — Transcrição Whisper

Coloque seus arquivos de áudio aqui para testar a qualidade da transcrição.

## Formatos suportados
`.mp3`, `.mp4`, `.mpeg`, `.mpga`, `.m4a`, `.wav`, `.webm`, `.ogg`, `.opus`

## Como testar

```bash
# Transcreve todos os áudios do diretório
python scripts/testar_transcricao.py

# Transcreve um arquivo específico
python scripts/testar_transcricao.py testes/audios/meu_audio.ogg

# Salva os resultados em arquivo
python scripts/testar_transcricao.py --salvar
```

## Sugestões de áudios para testar

Para validar o cenário real do AITrainer, grave áudios com:

1. Registro simples: *"Registra supino 80 kg, 4 séries, 10 repetições"*
2. Nome informal: *"Registra puxada alta 53 kg"*
3. Múltiplos exercícios: *"Fiz rosca 10 kg e remada 40 kg, 4 séries cada"*
4. Consulta: *"O que falta no treino de hoje?"*
5. Com ruído ambiente (academia): teste de robustez
