"""
Retrieval + generation — the exact logic from 03_retrieve.py and 04_answer.py,
adapted to run against a per-request DB connection and to support filtering
by document_id. The SQL query, the grounding prompt, and the streaming call
to the LLM are unchanged from the tested scripts.
"""

from collections.abc import Generator

from anthropic import Anthropic

from config import LLM_MAX_TOKENS, LLM_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL, TOP_K
from database import get_connection
from embeddings import embed

client = Anthropic(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)


def count_chunks(document_id: str | None = None) -> int:
    """How many chunks are available to search (optionally scoped to one document)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if document_id:
                cur.execute(
                    "SELECT COUNT(*) FROM chunks WHERE document_id = %s;", (document_id,)
                )
            else:
                cur.execute("SELECT COUNT(*) FROM chunks;")
            return cur.fetchone()[0]


def retrieve(question: str, document_id: str | None = None, top_k: int = TOP_K) -> list[str]:
    """Embed the question, then find the top_k most similar chunks (same as Stage 3/4)."""
    q_vector = embed(question)

    with get_connection() as conn:
        with conn.cursor() as cur:
            if document_id:
                cur.execute(
                    """
                    SELECT content FROM chunks
                    WHERE document_id = %s
                    ORDER BY embedding <=> %s
                    LIMIT %s;
                    """,
                    (document_id, q_vector, top_k),
                )
            else:
                cur.execute(
                    "SELECT content FROM chunks ORDER BY embedding <=> %s LIMIT %s;",
                    (q_vector, top_k),
                )
            return [row[0] for row in cur.fetchall()]


def build_prompt(chunks: list[str], question: str) -> str:
    """The grounding prompt — anti-hallucination rules unchanged, plus structuring guidance."""
    context = ""
    for i, chunk in enumerate(chunks):
        context += f"[Source {i + 1}] {chunk}\n\n"

    return f"""Answer the question using ONLY the context below.
If the answer is not in the context, say "I don't know based on the provided documents."
After each claim, cite the source number in brackets, like [Source 1].

Structure the answer for readability: use short paragraphs, and use "-" bullet
points when listing multiple facts or steps. Keep it concise.

Context:
{context}
Question: {question}"""


def stream_llm_response(prompt: str) -> Generator[str, None, None]:
    """Generate the grounded answer, streaming tokens live (same as 04_answer.py)."""
    try:
        with client.messages.stream(
            model=LLM_MODEL,
            max_tokens=LLM_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            yield from stream.text_stream
    except Exception as exc:
        yield f"\n\n[Error: the answer could not be completed — {exc}]"
