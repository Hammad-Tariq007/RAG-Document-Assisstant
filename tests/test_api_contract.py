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


@needs_db
def test_upload_unsupported_extension_returns_400():
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    r = client.post(
        "/upload",
        files={"file": ("virus.exe", b"MZ", "application/octet-stream")},
    )
    assert r.status_code == 400
    assert "detail" in r.json()
