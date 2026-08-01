import os
from pathlib import Path
from dotenv import load_dotenv


def get_database_dsn() -> str:
    """
    Retorna a connection string (DSN) para o PostgreSQL.

    Prioriza variáveis de ambiente (ideal para produção, como no Render) e,
    caso não estejam definidas, tenta carregar de um arquivo .env na raiz
    do projeto (útil para desenvolvimento local).

    Espera a variável: DATABASE_URL
    Exemplo:
      DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
    """
    # 1) Primeiro tenta pegar direto das variáveis de ambiente (Render, Docker, etc.)
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return dsn

    # 2) Fallback: tenta carregar de um arquivo .env na raiz do projeto (apenas dev)
    src_dir = Path(__file__).resolve().parents[2]
    project_root = src_dir.parent
    env_path = project_root / ".env"

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        dsn = os.getenv("DATABASE_URL")
        if dsn:
            return dsn

    # 3) Se chegou aqui, nem variável de ambiente nem .env forneceram a DATABASE_URL
    raise RuntimeError(
        "Variável DATABASE_URL não encontrada nas variáveis de ambiente "
        "nem em um arquivo .env na raiz do projeto."
    )




