from typing import Optional

from psycopg_pool import ConnectionPool

from src.Infrastructure.Database.Config import get_database_dsn
from src.SharedKernel.Logging.Logger import get_logger

_pool: Optional[ConnectionPool] = None
_logger = get_logger(__name__)


def _ensure_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        dsn = get_database_dsn()
        _logger.info("Inicializando pool de conexões com o PostgreSQL")
        _pool = ConnectionPool(
            conninfo=dsn,
            min_size=1,
            max_size=10,
            max_idle=30,  # segundos
            kwargs={"autocommit": True},
        )
    return _pool


def get_pool() -> ConnectionPool:
    """
    Retorna o pool de conexões, inicializando-o caso necessário.
    """
    return _ensure_pool()


def get_connection():
    """
    Context manager para obter uma conexão do pool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select 1")
    """
    pool = _ensure_pool()
    return pool.connection()


