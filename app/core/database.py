from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core import config

"""Configuração do banco de dados."""

engine = create_engine(
    config.DB_URL,
    pool_pre_ping=True,       # testa a conexão antes de usar — resolve "MySQL Connection not available"
    pool_recycle=1800,        # recicla conexões após 30 min (antes do timeout do MySQL de 8h)
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


def get_db():
    """Fornece uma sessão de banco para fluxos que usam injeção de dependência."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Base(DeclarativeBase):
    pass