from pathlib import Path
import subprocess
import sys

import pytest

"""Roda todos os testes de serviço para a aplicação."""


SERVICE_TESTS = [
    "testes/service/test_usuario_service.py",
    "testes/service/test_treino_service.py",
    "testes/service/test_exercicio_service.py",
    "testes/service/test_treino_exercicio.py",
    "testes/service/test_execucao_service.py",
    "testes/service/test_progresso_service.py",
    "testes/service/test_avaliacao_service.py",
    "testes/service/test_dash_board_service.py",
]


def _run_service_suite_subprocess() -> subprocess.CompletedProcess:
    repo_root = Path(__file__).resolve().parent.parent
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *SERVICE_TESTS],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )


def run_all_service_tests():
    result = _run_service_suite_subprocess()
    if result.returncode != 0:
        raise RuntimeError(
            "Falha ao executar a suíte de serviços.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    print("Todos os testes de serviço foram executados com sucesso.")


def test_service_suite() -> None:
    result = _run_service_suite_subprocess()
    assert result.returncode == 0, (
        "A suíte de serviços falhou.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


if __name__ == "__main__":
    run_all_service_tests()