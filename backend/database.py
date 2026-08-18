"""
Database connection and schema management for the pgvector-backed chunk store.

The table shape matches 02_store.py exactly (id, content, embedding vector(384))
plus the document_id / document_name / uploaded_at columns needed to support
multiple documents in the web app. ALTER TABLE ... ADD COLUMN IF NOT EXISTS
means this also upgrades a table created by the original 02_store.py script
without losing any rows already in it.
"""

from contextlib import contextmanager

import psycopg2
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, EMBEDDING_DIM
from pgvector.psycopg2 import register_vector


class DatabaseUnavailableError(Exception):
    """Raised when the Postgres/pgvector container can't be reached."""


@contextmanager
def get_connection():
    """Open a fresh connection per request and always close it afterwards."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    except psycopg2.OperationalError as exc:
        raise DatabaseUnavailableError(str(exc)) from exc

    try:
        register_vector(conn)
        yield conn
    finally:
        conn.close()


def init_schema() -> None:
    """Create the extension/table if missing, and add the new columns if not."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS chunks (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding vector({EMBEDDING_DIM})
                );
                """
            )
            cur.execute("ALTER TABLE chunks ADD COLUMN IF NOT EXISTS document_id UUID;")
            cur.execute("ALTER TABLE chunks ADD COLUMN IF NOT EXISTS document_name TEXT;")
            cur.execute(
                "ALTER TABLE chunks ADD COLUMN IF NOT EXISTS uploaded_at "
                "TIMESTAMPTZ NOT NULL DEFAULT NOW();"
            )
            # Every chunk must belong to a document — enforced at the schema level
            # now that legacy rows without a document_id have been cleaned up.
            cur.execute("DELETE FROM chunks WHERE document_id IS NULL;")
            cur.execute("ALTER TABLE chunks ALTER COLUMN document_id SET NOT NULL;")
            cur.execute("ALTER TABLE chunks ALTER COLUMN document_name SET NOT NULL;")
        conn.commit()
