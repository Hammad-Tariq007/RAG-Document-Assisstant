"""
FastAPI app for the document assistant.

Endpoints:
  POST   /upload              upload a supported document, chunk + embed + store it
  POST   /ask                 ask a question, get a streamed, cited, grounded answer
  GET    /documents           list uploaded documents
  DELETE /documents/{doc_id}  remove a document and its chunks
"""

import uuid
from contextlib import asynccontextmanager

from chunking import chunk_text
from database import DatabaseUnavailableError, get_connection, init_schema
from documents import extract_text
from embeddings import embed
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from rag import build_prompt, count_chunks, retrieve, stream_llm_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_schema()
    yield


app = FastAPI(title="Document Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DatabaseUnavailableError)
def handle_db_unavailable(request, exc: DatabaseUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": "The database is unreachable. Is the Docker container running?"},
    )


class AskRequest(BaseModel):
    question: str
    document_id: str | None = None


def _validate_document_id(document_id: str | None) -> None:
    if document_id is None:
        return
    try:
        uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id.") from None


@app.post("/upload")
async def upload_document(file: UploadFile):
    file_bytes = await file.read()
    text = extract_text(file.filename, file_bytes)

    chunks = chunk_text(text)
    document_id = str(uuid.uuid4())

    with get_connection() as conn:
        with conn.cursor() as cur:
            for chunk in chunks:
                vector = embed(chunk)
                cur.execute(
                    """
                    INSERT INTO chunks (content, embedding, document_id, document_name)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (chunk, vector, document_id, file.filename),
                )
        conn.commit()

    return {
        "document_id": document_id,
        "document_name": file.filename,
        "chunk_count": len(chunks),
    }


@app.post("/ask")
def ask_question(body: AskRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    _validate_document_id(body.document_id)

    if count_chunks(body.document_id) == 0:
        detail = (
            "No documents match that filter."
            if body.document_id
            else "No documents have been uploaded yet."
        )
        raise HTTPException(status_code=400, detail=detail)

    chunks = retrieve(question, document_id=body.document_id)
    prompt = build_prompt(chunks, question)

    return StreamingResponse(stream_llm_response(prompt), media_type="text/plain")


@app.get("/documents")
def list_documents():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT document_id, document_name, COUNT(*) AS chunk_count,
                       MIN(uploaded_at) AS uploaded_at
                FROM chunks
                WHERE document_id IS NOT NULL
                GROUP BY document_id, document_name
                ORDER BY MIN(uploaded_at) DESC;
                """
            )
            rows = cur.fetchall()

    return [
        {
            "document_id": str(row[0]),
            "document_name": row[1],
            "chunk_count": row[2],
            "uploaded_at": row[3].isoformat(),
        }
        for row in rows
    ]


@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    _validate_document_id(document_id)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chunks WHERE document_id = %s;", (document_id,))
            deleted = cur.rowcount
        conn.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {"document_id": document_id, "chunks_removed": deleted}
