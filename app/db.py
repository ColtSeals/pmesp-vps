from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Arquivo do banco (pmesp.db) vai ficar na raiz do projeto
DATABASE_URL = "sqlite:///./pmesp.db"

# Cria o "motor" de conexão com o banco
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # necessário para SQLite com FastAPI
)

# Sessão padrão (usada em cada requisição)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base para os modelos (tabelas)
Base = declarative_base()


def get_db():
    """Abre uma conexão com o banco para cada requisição e fecha ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
