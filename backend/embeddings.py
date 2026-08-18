"""
Embedding model singleton.

Loaded once at import time (same as the numbered scripts loading it once
at module scope) so every request reuses the same in-memory model instead
of reloading it per call.
"""

from config import EMBEDDING_MODEL_NAME
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed(text: str):
    """Text -> 384-dim vector, using the same model for indexing and querying."""
    return model.encode(text)
