import os
from pathlib import Path
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configura apenas o ambiente mínimo necessário para testes em SQLite.
# Nenhuma credencial de desenvolvimento deve ficar exposta no código.
os.environ.setdefault("DB_URL", "sqlite:///./testes/test.db")

from app.core.database import Base

# Importa modelos para registrar tabelas no metadata.
from app.models import avaliacao_fisica, dashboard_token, execucao, exercicio, treino, treino_exercicio, usuario

TEST_DB_PATH = Path(__file__).resolve().parent / "test.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture
def db_session_factory():
    return TestingSessionLocal


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()