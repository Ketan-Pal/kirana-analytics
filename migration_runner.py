import os
import re
import time
import hashlib
import psycopg2
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Load .env file
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")

class MigrationError(Exception):
    pass

class MigrationChecksumError(MigrationError):
    pass

def get_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment or .env file.")
    return psycopg2.connect(db_url)

def compute_checksum(content: str) -> str:
    """Computes SHA-256 checksum of SQL script content."""
    # Normalize line endings to avoid CRLF vs LF checksum discrepancies across platforms
    normalized = content.replace("\r\n", "\n").strip().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()

def ensure_schema_version_table(conn):
    """Ensures the schema_version audit table exists before running migrations."""
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            installed_rank SERIAL PRIMARY KEY,
            version VARCHAR(50) NOT NULL UNIQUE,
            description VARCHAR(200) NOT NULL,
            type VARCHAR(20) NOT NULL DEFAULT 'SQL',
            script VARCHAR(1000) NOT NULL,
            checksum VARCHAR(64) NOT NULL,
            installed_by VARCHAR(100) NOT NULL,
            installed_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            execution_time_ms INTEGER NOT NULL,
            success BOOLEAN NOT NULL
        );
        """)
    conn.commit()

def get_applied_migrations(conn) -> Dict[str, Dict[str, Any]]:
    """Fetches applied migrations from schema_version table."""
    with conn.cursor() as cur:
        cur.execute("SELECT version, description, script, checksum, success FROM schema_version ORDER BY installed_rank ASC")
        rows = cur.fetchall()
        return {
            row[0]: {
                "version": row[0],
                "description": row[1],
                "script": row[2],
                "checksum": row[3],
                "success": row[4]
            }
            for row in rows
        }

def discover_migration_files() -> List[Tuple[int, str, str, str]]:
    """
    Discovers all V<number>__<description>.sql files in migrations directory.
    Returns: [(version_int, version_str, description, filepath), ...] sorted by version.
    """
    if not os.path.exists(MIGRATIONS_DIR):
        os.makedirs(MIGRATIONS_DIR, exist_ok=True)
        return []

    pattern = re.compile(r"^V(\d+)__(.+)\.sql$")
    migrations = []

    for fname in os.listdir(MIGRATIONS_DIR):
        match = pattern.match(fname)
        if match:
            v_int = int(match.group(1))
            v_str = str(v_int)
            desc = match.group(2).replace("_", " ")
            fpath = os.path.join(MIGRATIONS_DIR, fname)
            migrations.append((v_int, v_str, desc, fpath, fname))

    migrations.sort(key=lambda x: x[0])
    return migrations

def run_migrations(verbose: bool = True) -> List[str]:
    """
    Executes Flyway-style migrations with checksum verification and transactional guarantees.
    """
    conn = get_connection()
    applied_versions = []

    try:
        ensure_schema_version_table(conn)
        applied = get_applied_migrations(conn)
        discovered = discover_migration_files()

        if verbose:
            print(f"[Flyway Migration Runner] Found {len(discovered)} migration script(s) in {MIGRATIONS_DIR}")
            print(f"[Flyway Migration Runner] Current database version count: {len(applied)}")

        for v_int, v_str, desc, fpath, fname in discovered:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            checksum = compute_checksum(content)

            if v_str in applied:
                existing = applied[v_str]
                if existing["checksum"] != checksum:
                    raise MigrationChecksumError(
                        f"Checksum mismatch for migration {fname} (Version {v_str})!\n"
                        f"Applied checksum: {existing['checksum']}\n"
                        f"Local file checksum: {checksum}\n"
                        f"Flyway integrity policy prevents modifying applied migrations in production."
                    )
                if verbose:
                    print(f"  [Skipped] V{v_str} - {desc} (Already applied)")
                continue

            # Execute pending migration inside a dedicated transaction
            if verbose:
                print(f"  [Applying] V{v_str} - {desc} ({fname})...")

            start_time = time.time()
            try:
                with conn.cursor() as cur:
                    cur.execute(content)
                    exec_ms = int((time.time() - start_time) * 1000)
                    cur.execute("""
                        INSERT INTO schema_version (
                            version, description, type, script, checksum, installed_by, execution_time_ms, success
                        ) VALUES (%s, %s, 'SQL', %s, %s, %s, %s, TRUE)
                    """, (v_str, desc, fname, checksum, "migration_runner", exec_ms))

                conn.commit()
                applied_versions.append(f"V{v_str}: {desc}")
                if verbose:
                    print(f"  [Success] V{v_str} applied in {exec_ms}ms")
            except Exception as e:
                conn.rollback()
                # Log failed attempt if possible
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO schema_version (
                                version, description, type, script, checksum, installed_by, execution_time_ms, success
                            ) VALUES (%s, %s, 'SQL', %s, %s, %s, 0, FALSE)
                        """, (v_str, desc, fname, checksum, "migration_runner"))
                    conn.commit()
                except Exception:
                    pass
                raise MigrationError(f"Failed applying migration {fname}: {e}") from e

        if verbose:
            if applied_versions:
                print(f"[Flyway Migration Runner] Successfully applied {len(applied_versions)} migration(s).")
            else:
                print("[Flyway Migration Runner] Schema is up to date. No pending migrations.")

        return applied_versions

    finally:
        conn.close()

if __name__ == "__main__":
    run_migrations(verbose=True)
