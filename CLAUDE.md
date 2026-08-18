# Project Instructions

## Commands

Declared in `agent.config.json` -> `commands`. **Read that file; do not guess.**
An empty string means that step does not exist here: skip it, do not improvise a substitute.

## Project

**RAG Document Assistant** - upload PDF/DOCX/TXT, ask questions, get grounded answers
with `[Source N]` citations, streamed token-by-token.

**Stack**
- Backend: Python 3.11+, FastAPI, uvicorn on port 8001
- Frontend: Next.js 16 (App Router), React 19, TypeScript, Tailwind
- Vector store: PostgreSQL + pgvector in Docker on port **5433** (not 5432)
- Embeddings: `sentence-transformers` `all-MiniLM-L6-v2`, **384 dimensions**
- LLM: `anthropic/claude-haiku-4.5` via the Anthropic SDK pointed at OpenRouter
- Chunking: LangChain `RecursiveCharacterTextSplitter`, size 500, overlap 100

**Imports are flat, not package-style.** `backend/` is on the path, so modules import
each other directly: `from config import CHUNK_SIZE`, not `from backend.config import ...`.
Tests follow the same convention.

**Layout**
```
backend/
  config.py      settings: model names, chunk size, top_k, allowed extensions
  database.py    pgvector connection + schema migration on startup  [PROTECTED]
  embeddings.py  SentenceTransformer singleton - do not instantiate elsewhere
  chunking.py    chunk_text() - splitter wrapper
  documents.py   extract_text() - PDF/DOCX/TXT extraction
  rag.py         retrieve() + build_prompt() + stream_llm_response()
  main.py        FastAPI routes
frontend/src/
  app/           App Router layout + page
  components/    DocumentPanel, ChatPanel, MarkdownAnswer, ToastProvider
  lib/           api.ts (fetch + streaming client), types.ts
tests/           pytest suite; conftest.py provides the `needs_db` skip marker
0X_*.py          root-level reference/eval scripts - NOT imported by the app
```

**Data flow**
Upload -> extract text -> chunk (500/100) -> embed (384-dim) -> insert into `chunks`
with `document_id` + `document_name`.
Ask -> embed question -> `ORDER BY embedding <=> question_vector LIMIT 3`
(optionally scoped to one `document_id`) -> build grounding prompt -> stream from LLM.

**Conventions**
- Errors return `{"detail": "..."}` with a real status code: `400` invalid input,
  `404` missing document, `503` Postgres unreachable. Keep this shape.
- Settings live in `backend/config.py`. Never hard-code a model name, chunk size,
  `top_k`, or allowed-extension list inline.
- Answers stream. Do not convert a streaming endpoint to a blocking one.
- Frontend calls the backend only through `src/lib/api.ts`. No stray `fetch()` in components.
- Tests that need Postgres use the `needs_db` marker so they SKIP when it is down.
  A missing database must never look like a code failure.

**Landmines**
- The embedding dimension (384) is baked into the pgvector column. Changing the
  embedding model without a migration corrupts the store silently. Never do it.
- `backend/database.py` is a protected path - it owns schema migration. Propose
  changes in `REPORT.md`; do not edit it.
- The grounding prompt in `rag.py` is the entire anti-hallucination mechanism.
  Do not reword, soften, or "improve" it as a side effect of another change.
- Root-level `0X_*.py` scripts are standalone references. Do not refactor them into
  the app, and do not import app modules into them.

## Absolute rules

1. **`.tickets/<id>/SPEC.md` is frozen.** Never edit it. If it looks wrong, say so in
   `REPORT.md` and stop.
2. **Never weaken a test to make it pass.** No deleted cases, no loosened assertions,
   no `@pytest.mark.skip`, no `.skip`/`.only`, no widened tolerances.
3. **Never hard-code a value to satisfy a specific test input.** If it only works for
   the cases in the test file, it is not a fix.
4. **Never touch protected paths** (`agent.config.json` -> `policy.protected_paths`).
   If the ticket requires it, stop and park.
5. **Never commit secrets.** Add new variables to `.env.example` and document them
   in `REPORT.md`.
6. **Never run destructive git commands.** No force push, no hard reset, no history rewrite.
7. **Never add a dependency** without stating it explicitly in `REPORT.md`.
8. **You are the only writer.** Subagents you invoke are read-only.

## Definition of done

- Every acceptance criterion in `SPEC.md` is satisfied by the actual code.
- `pytest -q` and `ruff check .` both pass.
- The change is minimal - no unrelated refactors, no drive-by formatting.
- `REPORT.md` exists and is honest about what was not done.

## Honesty requirements

`REPORT.md` must state: what changed, what was verified and by which command,
**what was NOT done and why**, assumptions made, anything needing a human decision,
and any new dependency.

An accurate report of partial success is a better outcome than a confident report of
false success. You will not be penalised for saying a ticket could not be completed.
