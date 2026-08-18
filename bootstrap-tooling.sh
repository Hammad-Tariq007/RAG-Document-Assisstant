#!/usr/bin/env bash
# bootstrap-tooling.sh - run ONCE from the repo root.
# Adds the test/lint tooling this repo lacks. Without it the harness has nothing
# to verify the agent's work against.
set -euo pipefail
[ -d backend ] && [ -d frontend ] || { echo "Run this from the repo root."; exit 1; }

echo "==> requirements-dev.txt"
cat > requirements-dev.txt <<'EOF'
pytest>=8.0
pytest-asyncio>=0.23
httpx>=0.27
ruff>=0.5
EOF

echo "==> pyproject.toml (ruff + pytest config)"
cat > pyproject.toml <<'EOF'
[tool.ruff]
line-length = 100
target-version = "py311"
exclude = [".venv", "frontend", "node_modules"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = [".", "backend"]
addopts = "-q"
EOF

echo "==> tests/"
mkdir -p tests
cat > tests/conftest.py <<'EOF'
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
EOF

cat > tests/test_chunking.py <<'EOF'
"""Pure-logic tests: no database, no network, no model download."""

from chunking import chunk_text


def test_chunk_text_returns_list_of_strings():
    chunks = chunk_text("hello world. " * 200)
    assert isinstance(chunks, list)
    assert all(isinstance(c, str) for c in chunks)


def test_chunk_text_splits_long_input():
    assert len(chunk_text("word " * 2000)) > 1


def test_chunk_text_short_input_stays_single_chunk():
    assert len(chunk_text("short text")) == 1


def test_chunk_text_empty_input_does_not_crash():
    assert isinstance(chunk_text(""), list)
EOF

cat > tests/test_api_contract.py <<'EOF'
"""Error-shape contract tests. The API must return {"detail": "..."} with real codes."""

from conftest import needs_db


@needs_db
def test_ask_with_empty_question_returns_400():
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    r = client.post("/ask", json={"question": ""})
    assert r.status_code == 400
    assert "detail" in r.json()


@needs_db
def test_delete_invalid_document_id_returns_400():
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    r = client.delete("/documents/not-a-uuid")
    assert r.status_code == 400
    assert "detail" in r.json()
EOF

echo "==> frontend lint + typecheck scripts"
cd frontend
node -e '
const fs = require("fs");
const p = JSON.parse(fs.readFileSync("package.json", "utf8"));
p.scripts = p.scripts || {};
p.scripts.lint      = p.scripts.lint      || "next lint";
p.scripts.typecheck = p.scripts.typecheck || "tsc --noEmit";
fs.writeFileSync("package.json", JSON.stringify(p, null, 2) + "\n");
console.log("  ok");
'
cd ..

echo
echo "Done. Next:"
echo "  python3 -m venv .venv && source .venv/bin/activate"
echo "  pip install -r backend/requirements.txt -r requirements-dev.txt"
echo "  ruff check --fix . && ruff check ."
echo "  pytest -q"
