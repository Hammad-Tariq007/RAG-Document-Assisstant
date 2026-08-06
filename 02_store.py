import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from importlib import import_module

# Reuse the chunking code from Stage 1 (01_chunk.py)
chunk_module = import_module("01_chunk")
load_document = chunk_module.load_document
chunk_text = chunk_module.chunk_text

# ---- 1. Connect to the pgvector database ----
conn = psycopg2.connect(
    host="localhost",
    port=5433,                 # our RAG container's port (not the default 5432!)
    dbname="ragdb",
    user="postgres",
    password="ragpass",
)
conn.autocommit = True
cur = conn.cursor()

# ---- 2. Enable the pgvector extension + create the table ----
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
register_vector(conn)          # teaches psycopg2 how to handle vector columns

cur.execute("DROP TABLE IF EXISTS chunks;")   # fresh start each run (fine for learning)
cur.execute("""
    CREATE TABLE chunks (
        id      SERIAL PRIMARY KEY,
        content TEXT,
        embedding vector(384)          -- must match the model's 384 dimensions
    );
""")
print("Table 'chunks' created.")

# ---- 3. Load, chunk, embed, and insert ----
model = SentenceTransformer("all-MiniLM-L6-v2")

text = load_document("sample.txt")
chunks = chunk_text(text)
print(f"Embedding and storing {len(chunks)} chunks...")

for chunk in chunks:
    embedding = model.encode(chunk)            # text -> 384-dim vector
    cur.execute(
        "INSERT INTO chunks (content, embedding) VALUES (%s, %s);",
        (chunk, embedding),                    # store the text AND its vector
    )

# ---- 4. Verify what's in the database ----
cur.execute("SELECT COUNT(*) FROM chunks;")
count = cur.fetchone()[0]
print(f"Done. {count} chunks are now stored in the database.")

cur.close()
conn.close()