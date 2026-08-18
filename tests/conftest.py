import os

import pytest


def _db_available() -> bool:
    try:
        import psycopg2

        psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5433"),
            dbname=os.getenv("DB_NAME", "ragdb"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "ragpass"),
            connect_timeout=2,
        ).close()
        return True
    except Exception:
        return False


# DB-dependent tests SKIP when Postgres is down. They must never FAIL for that
# reason, or the harness cannot tell "agent broke it" from "database wasn't up".
needs_db = pytest.mark.skipif(not _db_available(), reason="Postgres on :5433 unavailable")
