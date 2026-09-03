"""
Script para testar a qualidade da transcrição Whisper.

Transcreve todos os áudios em testes/audios/ e exibe os resultados
com tempo de processamento e qualidade estimada.

Uso:
    python scripts/testar_transcricao.py
    python scripts/testar_transcricao.py testes/audios/meu_audio.ogg
    python scripts/testar_transcricao.py --salvar
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Garante que o root do projeto está no path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.service.transcricao_service import TranscricaoService, _EXTENSOES_SUPORTADAS

AUDIOS_DIR = ROOT / "testes" / "audios"
RESULTADOS_FILE = ROOT / "testes" / "audios" / "resultados_transcricao.txt"


def _barra(valor: float, maximo: float = 1.0, largura: int = 20) -> str:
    preenchido = int((valor / maximo) * largura)
    return "█" * preenchido + "░" * (largura - preenchido)


def transcrever_arquivo(service: TranscricaoService, caminho: Path) -> dict:
    inicio = time.perf_counter()
    try:
        texto = service.transcrever_arquivo(caminho)
        duracao = time.perf_counter() - inicio
        return {
            "arquivo": caminho.name,
            "texto": texto,
            "duracao_s": round(duracao, 2),
            "palavras": len(texto.split()),
            "sucesso": True,
            "erro": None,
        }
    except Exception as e:
        duracao = time.perf_counter() - inicio
        return {
            "arquivo": caminho.name,
            "texto": None,
            "duracao_s": round(duracao, 2),
            "palavras": 0,
            "sucesso": False,
            "erro": str(e),
        }


def main():
    salvar = "--salvar" in sys.argv
    args_arquivos = [a for a in sys.argv[1:] if not a.startswith("--")]

    try:
        service = TranscricaoService()
    except ValueError as e:
        print(f"❌ {e}")
        print("Configure GROQ_API_KEY no .env")
        sys.exit(1)

    # Define quais arquivos processar
    if args_arquivos:
        arquivos = [Path(a) for a in args_arquivos]
    else:
        arquivos = [
            f for f in sorted(AUDIOS_DIR.iterdir())
            if f.suffix.lower() in _EXTENSOES_SUPORTADAS
        ]

    if not arquivos:
        print(f"Nenhum áudio encontrado em {AUDIOS_DIR}")
        print(f"Formatos suportados: {', '.join(sorted(_EXTENSOES_SUPORTADAS))}")
        print("Leia testes/audios/README.md para instruções.")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  AITrainer — Teste de Qualidade de Transcrição")
    print(f"  Modelo: whisper-large-v3-turbo (Groq)")
    print(f"{'='*60}\n")

    resultados = []
    for caminho in arquivos:
        print(f"🎙  Transcrevendo: {caminho.name} ...", end=" ", flush=True)
        resultado = transcrever_arquivo(service, caminho)
        resultados.append(resultado)

        if resultado["sucesso"]:
            print(f"✓ ({resultado['duracao_s']}s)")
        else:
            print(f"✗ ERRO")

    # Exibe resultados detalhados
    print(f"\n{'─'*60}")
    linhas_saida = []

    for r in resultados:
        linha_header = f"\n📄 {r['arquivo']}  ({r['duracao_s']}s)"
        print(linha_header)
        linhas_saida.append(linha_header)

        if r["sucesso"]:
            linha_texto = f"   \"{r['texto']}\""
            linha_stats = f"   {r['palavras']} palavras"
            print(linha_texto)
            print(linha_stats)
            linhas_saida.extend([linha_texto, linha_stats])
        else:
            linha_erro = f"   ❌ {r['erro']}"
            print(linha_erro)
            linhas_saida.append(linha_erro)

    # Resumo
    sucessos = [r for r in resultados if r["sucesso"]]
    falhas = [r for r in resultados if not r["sucesso"]]
    tempo_total = sum(r["duracao_s"] for r in resultados)

    resumo = (
        f"\n{'='*60}\n"
        f"  Resumo: {len(sucessos)}/{len(resultados)} transcrições OK\n"
        f"  Tempo total: {tempo_total:.1f}s  |  Média: {tempo_total/len(resultados):.1f}s por áudio\n"
    )
    if falhas:
        resumo += f"  Falhas: {', '.join(r['arquivo'] for r in falhas)}\n"
    resumo += f"{'='*60}\n"

    print(resumo)
    linhas_saida.append(resumo)

    if salvar:
        RESULTADOS_FILE.write_text("\n".join(linhas_saida), encoding="utf-8")
        print(f"Resultados salvos em: {RESULTADOS_FILE}")


if __name__ == "__main__":
    main()
