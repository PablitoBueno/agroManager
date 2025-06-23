import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base  # importa o Base com todos os seus modelos

# URL de conexão ao PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://usuario:senha123@localhost/cooperativa_agricola"
)

# cria o engine com configurações otimizadas
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # Verifica conexões antes de usar
    pool_size=5,               # Número máximo de conexões no pool
    max_overflow=10,           # Conexões adicionais além do pool_size
    pool_recycle=3600,         # Recicla conexões após 1 hora
    echo=False                 # Desativa logs SQL (altere para True para debug)
)

# fábrica de sessões com configurações seguras
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False     # Evita problemas com objetos expirados
)

def init_db():
    """
    Cria todas as tabelas no banco de forma segura.
    """
    # Cria as tabelas apenas se não existirem (comportamento padrão do SQLAlchemy)
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Dependência FastAPI: fornece uma sessão por requisição.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Garante que a sessão será fechada

def get_connection():
    """
    Obtém uma conexão direta com o banco (para operações não ORM).
    """
    return engine.connect()