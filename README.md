<div align="center">

# Document Assistant

**Upload documents. Ask questions. Get grounded, cited answers — streamed live.**

A full-stack Retrieval-Augmented Generation (RAG) application combining a
pgvector-backed semantic search pipeline with a FastAPI backend and a
Next.js frontend.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL%20%2B%20pgvector-4169E1?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [How Grounding Works](#how-grounding-works)
- [Roadmap](#roadmap)
- [Author](#author)

## Overview

Document Assistant lets you drop in a PDF, Word, or text file and immediately
start asking questions about it. Answers are never invented — every response
is generated strictly from the content you uploaded, with inline `[Source N]`
citations pointing back to the exact chunk used, and streamed token-by-token
so the UI feels alive rather than a spinner-then-dump experience.

Under the hood it's a classic RAG pipeline: chunk → embed → store in a vector
database → semantically retrieve the most relevant chunks for a question →
feed them to an LLM constrained by a strict grounding prompt.

## Features

- **Multi-format ingestion** — `.pdf`, `.docx`, `.txt`, `.md`, and `.csv`, parsed and chunked automatically
- **Semantic retrieval** — cosine similarity search over `sentence-transformers` embeddings via pgvector
- **Grounded, cited answers** — the model is instructed to answer *only* from retrieved context and to cite `[Source N]`; it says "I don't know" when the answer isn't in the documents
- **Live token streaming** — answers render live via a streamed HTTP response, not a blocking request
- **Structured responses** — answers are formatted with headings, bullet points, and bold text where it improves readability, rendered as Markdown in the UI
- **Per-document scoping** — ask questions across the entire knowledge base or filter to a single uploaded document
- **Document management** — drag-and-drop upload, live list with chunk counts, one-click delete
- **Polished UI** — minimalist, responsive interface with toasts, loading states, and empty states

## Architecture

```
┌──────────────────┐        ┌────────────────────────┐        ┌──────────────────────┐
│   Next.js UI      │  HTTP  │    FastAPI backend      │  SQL   │  PostgreSQL + pgvector │
│   (frontend/)      │───────▶│    (backend/)            │───────▶│  "chunks" table         │
│                    │        │                          │        │  (Docker, :5433)        │
│  • Upload panel     │        │  upload → extract text   │        └──────────────────────┘
│  • Streaming chat   │◀───────│  → chunk → embed → store │
│  • Citation render  │  SSE-  │  ask → embed → retrieve  │
└──────────────────┘  style   │  → grounding prompt      │
                       stream  │  → stream from LLM       │
                                └────────────┬────────────┘
                                             │ Anthropic SDK (via OpenRouter)
                                             ▼
                                   anthropic/claude-haiku-4.5
```

**Request flow:**

1. **Upload** — extract text (`pypdf` for PDFs, `python-docx` for Word docs,
   plain decode for text files) → split into overlapping chunks via
   `RecursiveCharacterTextSplitter` (chunk_size=500, overlap=100) → embed each
   chunk with `all-MiniLM-L6-v2` (384 dimensions) → persist to `chunks`,
   tagged with a `document_id` and `document_name`.
2. **Ask** — embed the question with the same model → pgvector cosine search
   (`ORDER BY embedding <=> question_vector LIMIT 3`, optionally scoped to one
   document) → assemble the grounding prompt → stream the answer from Claude
   token-by-token straight through to the browser.

## Tech Stack

| Layer            | Technology                                                        |
|-------------------|--------------------------------------------------------------------|
| Frontend           | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS       |
| Backend            | FastAPI, Python 3.11+                                              |
| Vector database    | PostgreSQL + pgvector                                              |
| Embeddings         | `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim)              |
| Chunking           | LangChain `RecursiveCharacterTextSplitter`                         |
| LLM                | Claude (`anthropic/claude-haiku-4.5`) via the Anthropic SDK + OpenRouter |
| File parsing       | `pypdf`, `python-docx`                                             |

## Project Structure

```
rag-document-assistant/
├── .env.example              # environment variable template (copy to .env)
├── 01_chunk.py                # chunking logic (reference implementation)
├── 02_store.py                # embedding + storage logic (reference implementation)
├── 03_retrieve.py             # retrieval logic (reference implementation)
├── 04_answer.py               # grounded generation logic (reference implementation)
├── 05_eval.py                 # retrieval evaluation harness
├── 06_eval_generation.py      # generation evaluation harness (LLM-as-judge)
├── sample.txt                 # sample document for quick testing
│
├── backend/
│   ├── config.py               # centralized config: model names, chunk size, top_k, etc.
│   ├── database.py             # pgvector connection handling + schema migrations
│   ├── embeddings.py           # SentenceTransformer singleton
│   ├── chunking.py             # RecursiveCharacterTextSplitter wrapper
│   ├── documents.py            # PDF / DOCX / TXT / MD / CSV text extraction
│   ├── rag.py                  # retrieve() + build_prompt() + stream_llm_response()
│   ├── main.py                 # FastAPI app and route handlers
│   └── requirements.txt
│
└── frontend/
    ├── .env.example             # environment variable template
    └── src/
        ├── app/                  # App Router entrypoints (layout, page)
        ├── components/           # DocumentPanel, ChatPanel, MarkdownAnswer, ToastProvider
        └── lib/                  # api.ts (fetch + streaming client), types.ts
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker
- An [OpenRouter](https://openrouter.ai/) API key

### 1. Clone and configure

```bash
git clone https://github.com/Hammad-Tariq007/RAG-Document-Assisstant.git
cd RAG-Document-Assisstant
cp .env.example .env          # then fill in OPENROUTER_API_KEY
cp frontend/.env.example frontend/.env.local
```

### 2. Start the vector database

```bash
docker run -d --name rag-postgres -p 5433:5432 \
  -e POSTGRES_PASSWORD=ragpass -e POSTGRES_DB=ragdb \
  pgvector/pgvector:pg16
```

### 3. Start the backend

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt

cd backend
uvicorn main:app --port 8001
```

The backend creates and migrates the `chunks` table automatically on
startup. API docs are available at `http://127.0.0.1:8001/docs`.

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** and start uploading documents.

## Environment Variables

**`.env`** (project root, read by the backend):

| Variable              | Description                                   | Default        |
|------------------------|------------------------------------------------|-----------------|
| `OPENROUTER_API_KEY`   | API key for the Anthropic SDK via OpenRouter   | —               |
| `DB_HOST`              | Postgres host                                   | `localhost`     |
| `DB_PORT`              | Postgres port                                   | `5433`          |
| `DB_NAME`              | Database name                                   | `ragdb`         |
| `DB_USER`              | Database user                                   | `postgres`      |
| `DB_PASSWORD`          | Database password                               | `ragpass`       |

**`frontend/.env.local`:**

| Variable                | Description               | Default                    |
|---------------------------|----------------------------|------------------------------|
| `NEXT_PUBLIC_API_URL`     | Base URL of the backend    | `http://127.0.0.1:8001`     |

## API Reference

| Method   | Endpoint                     | Description                                                  |
|-----------|-------------------------------|----------------------------------------------------------------|
| `POST`    | `/upload`                     | Upload a `.pdf` / `.docx` / `.txt` / `.md` / `.csv` file — chunks, embeds, and stores it |
| `POST`    | `/ask`                        | `{ question, document_id? }` → streamed, cited, grounded answer |
| `GET`     | `/documents`                  | List all uploaded documents                                    |
| `DELETE`  | `/documents/{document_id}`    | Remove a document and all of its chunks                        |

Errors return JSON (`{"detail": "..."}`) with an appropriate status code:
`400` for invalid input (bad file type, empty question, empty knowledge
base), `404` when deleting a document that doesn't exist, `503` if Postgres
is unreachable.

## How Grounding Works

The core anti-hallucination behavior is a single, deliberately strict
instruction sent alongside the retrieved context:

> Answer the question using ONLY the context below. If the answer is not in
> the context, say "I don't know based on the provided documents." After
> each claim, cite the source number in brackets, like `[Source 1]`.

This means the model cannot answer from general knowledge — only from what
you've actually uploaded — and every factual claim is traceable back to a
specific chunk.

## Roadmap

- [ ] Multi-turn conversational memory
- [ ] Re-ranking of retrieved chunks before generation
- [ ] Support for additional file types (`.md`, `.csv`)
- [ ] User authentication and per-user document isolation

## Author

**Hammad Tariq**
[GitHub @Hammad-Tariq007](https://github.com/Hammad-Tariq007)
