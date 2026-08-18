"""
Central configuration for the backend.

All values here mirror the exact settings already tested in the numbered
scripts at the project root (01_chunk.py .. 04_answer.py). Nothing about
the embedding model, chunking parameters, or grounding prompt is changed —
this module just centralizes them so main.py and rag.py don't repeat them.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# The scripts at the project root load ".env" from their own working
# directory. The backend lives one level down, so point at the same file
# explicitly instead of duplicating secrets into a second .env.
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# ---- Database (Postgres + pgvector, Docker container on localhost:5433) ----
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5433")
DB_NAME = os.environ.get("DB_NAME", "ragdb")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "ragpass")

# ---- Embeddings (must match what was used to build the index) ----
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# ---- Chunking (same as 01_chunk.py) ----
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
CHUNK_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

# ---- Retrieval ----
TOP_K = 3

# ---- LLM (Anthropic SDK pointed at OpenRouter) ----
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api"
LLM_MODEL = "anthropic/claude-haiku-4.5"
LLM_MAX_TOKENS = 500  # a little extra headroom for bulleted/structured answers

# ---- Uploads ----
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md", ".csv"}
