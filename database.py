import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from migration_runner import run_migrations

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

def get_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set in environment or .env file.")
    
    # Connect to Supabase PostgreSQL with dictionary row factory
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    return conn

def init_db():
    """Initializes the database by applying all pending Flyway-style migrations."""
    run_migrations(verbose=True)

if __name__ == "__main__":
    init_db()
