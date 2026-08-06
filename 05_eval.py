import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

conn = psycopg2.connect(
    host="localhost", port=5433, dbname="ragdb",
    user="postgres", password="ragpass",
)
register_vector(conn)
cur = conn.cursor()
embed_model = SentenceTransformer("all-MiniLM-L6-v2")


def retrieve(question: str, top_k: int = 3):
    q_vector = embed_model.encode(question)
    cur.execute(
        "SELECT content FROM chunks ORDER BY embedding <=> %s LIMIT %s;",
        (q_vector, top_k),
    )
    return [row[0] for row in cur.fetchall()]


# ---- The eval dataset: questions + a keyword that MUST appear in the right chunk ----
# Each test says: "when I ask this, the correct chunk should contain this keyword."
eval_set = [
    {"question": "What did Hammad build for the business development team?", "expected_keyword": "CRM"},
    {"question": "Where did Hammad study?",                                  "expected_keyword": "PUCIT"},
    {"question": "Tell me about the security project.",                      "expected_keyword": "Vaultwarden"},
    {"question": "What was Hammad's final year project?",                    "expected_keyword": "Fitness Freaks"},
    {"question": "What real-time social media platform did he build?",       "expected_keyword": "Kiooki"},
]


def evaluate_retrieval(top_k: int = 3):
    hits = 0
    print(f"Evaluating retrieval (top_k={top_k}) on {len(eval_set)} questions:\n")

    for test in eval_set:
        question = test["question"]
        keyword = test["expected_keyword"]

        retrieved_chunks = retrieve(question, top_k=top_k)
        # A "hit" = the expected keyword appears in ANY of the retrieved chunks
        found = any(keyword.lower() in chunk.lower() for chunk in retrieved_chunks)

        if found:
            hits += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"[{status}] {question}")
        print(f"        expected keyword: '{keyword}'\n")

    score = hits / len(eval_set)
    print(f"Retrieval score: {hits}/{len(eval_set)} = {score:.0%}")
    return score


if __name__ == "__main__":
    evaluate_retrieval(top_k=3)
    cur.close()
    conn.close()