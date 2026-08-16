from pathlib import Path
import subprocess
import sys

import pytest

"""Roda todos os testes de tools para a aplicação."""


TOOLS_TESTS = [
    "testes/tools/test_usuario_tools.py",
    "testes/tools/test_treino_tools.py",
    "testes/tools/test_treino_exercicio_tools.py",
    "testes/tools/test_execucao_tools.py",
    "testes/tools/test_avaliacao_fisica_tools.py",
    "testes/tools/test_progresso_e_exercicio_tools.py",
    "testes/tools/test_dashboard_tools.py",
]


def _run_tools_suite_subprocess() -> subprocess.CompletedProcess:
    repo_root = Path(__file__).resolve().parent.parent
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *TOOLS_TESTS],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )


def run_all_tools_tests():
    result = _run_tools_suite_subprocess()
    if result.returncode != 0:
        raise RuntimeError(
            "Falha ao executar a suíte de tools.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    print("Todos os testes de tools foram executados com sucesso.")


def test_tools_suite() -> None:
    result = _run_tools_suite_subprocess()
    assert result.returncode == 0, (
        "A suíte de tools falhou.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


if __name__ == "__main__":
    run_all_tools_tests()
