from contextlib import contextmanager
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from config import settings
from logging_config import get_logger
from migration_runner import run_migrations

logger = get_logger("database")

_pool = None

def get_pool():
    """Lazily initializes and returns the ThreadedConnectionPool."""
    global _pool
    if _pool is None or _pool.closed:
        try:
            _pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=settings.database_url,
                cursor_factory=RealDictCursor
            )
            logger.info("Initialized ThreadedConnectionPool for Supabase PostgreSQL (1-10 connections).")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    return _pool

@contextmanager
def get_db():
    """Context manager yielding a pooled database connection and guaranteeing return to pool."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

@contextmanager
def get_db_cursor(commit: bool = False):
    """Context manager yielding a RealDictCursor with optional auto-commit on exit."""
    with get_db() as conn:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()

def get_connection():
    """Direct connection fallback for standalone scripts or legacy callers."""
    return psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)

def init_db():
    """Initializes the database by applying all pending Flyway-style migrations."""
    run_migrations(verbose=True)

if __name__ == "__main__":
    init_db()
