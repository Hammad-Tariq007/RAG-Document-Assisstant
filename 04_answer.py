import os

import psycopg2
from anthropic import Anthropic
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

load_dotenv()

# ---- Database + embedding model (same as Stage 3) ----
conn = psycopg2.connect(
    host="localhost", port=5433, dbname="ragdb",
    user="postgres", password="ragpass",
)
register_vector(conn)
cur = conn.cursor()
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# ---- Claude client ----
client = Anthropic(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api",
)


def retrieve(question: str, top_k: int = 3):
    q_vector = embed_model.encode(question)
    cur.execute(
        "SELECT content FROM chunks ORDER BY embedding <=> %s LIMIT %s;",
        (q_vector, top_k),
    )
    return [row[0] for row in cur.fetchall()]


def answer(question: str) -> str:
    # 1. RETRIEVE the relevant chunks
    chunks = retrieve(question)

    # 2. Build the context, numbering each chunk so the model can cite it
    context = ""
    for i, chunk in enumerate(chunks):
        context += f"[Source {i + 1}] {chunk}\n\n"

    # 3. The grounding prompt — the anti-hallucination instructions
    prompt = f"""Answer the question using ONLY the context below.
If the answer is not in the context, say "I don't know based on the provided documents."
After each claim, cite the source number in brackets, like [Source 1].

Context:
{context}
Question: {question}"""

    # 4. GENERATE the grounded answer — STREAMING this time
    full_answer = ""
    with client.messages.stream(
        model="anthropic/claude-haiku-4.5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)     # print each piece live
            full_answer += text                 # also collect the full text
    print()                                     # newline after streaming ends

    return full_answer                          # return the complete answer for later use


if __name__ == "__main__":
    question = "What did Hammad build for the business development team?"
    print(f"Question: {question}\n")
    print("Answer:")
    answer(question)                            # it now streams as it prints

    cur.close()
    conn.close()