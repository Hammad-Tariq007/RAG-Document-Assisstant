import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

# ---- Connect to the same database ----
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    dbname="ragdb",
    user="postgres",
    password="ragpass",
)
register_vector(conn)
cur = conn.cursor()

# ---- Load the SAME embedding model used to store the chunks ----
model = SentenceTransformer("all-MiniLM-L6-v2")


def retrieve(question: str, top_k: int = 3):
    """Embed the question, then find the top_k most similar chunks."""
    q_vector = model.encode(question)          # question -> vector (same model!)

    cur.execute(
        """
        SELECT content, embedding <=> %s AS distance
        FROM chunks
        ORDER BY distance
        LIMIT %s;
        """,
        (q_vector, top_k),
    )
    return cur.fetchall()                       # list of (content, distance) rows


if __name__ == "__main__":
    question = "What did Hammad build for the business development team?"
    print(f"Question: {question}\n")

    results = retrieve(question)
    print(f"Top {len(results)} most relevant chunks:\n")

    for i, (content, distance) in enumerate(results):
        print(f"--- Result {i + 1} (distance: {distance:.4f}) ---")
        print(content)
        print()

    cur.close()
    conn.close()