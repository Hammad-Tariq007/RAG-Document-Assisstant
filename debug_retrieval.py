import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

conn = psycopg2.connect(
    host="localhost", port=5433, dbname="ragdb",
    user="postgres", password="ragpass",
)
register_vector(conn)
cur = conn.cursor()
model = SentenceTransformer("all-MiniLM-L6-v2")

question = "What does Hammad do?"
q_vector = model.encode(question)

# Show ALL chunks ranked by distance, so we see where the right one landed
cur.execute(
    "SELECT content, embedding <=> %s AS distance FROM chunks ORDER BY distance;",
    (q_vector,),
)

print(f"Question: {question}\n")
print("ALL chunks ranked by distance (closest first):\n")
for i, (content, distance) in enumerate(cur.fetchall()):
    marker = "  <-- has 'Fitness Freaks'" if "Fitness Freaks" in content else ""
    print(f"Rank {i + 1} | distance {distance:.4f}{marker}")
    print(f"   {content[:90]}...")
    print()

cur.close()
conn.close()