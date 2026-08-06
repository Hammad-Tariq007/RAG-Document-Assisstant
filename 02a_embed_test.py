from sentence_transformers import SentenceTransformer

# Downloads the model the first time (~90 MB), then caches it locally.
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

text = "Hammad works at Meissasoft."
vector = model.encode(text)

print("Text:", text)
print("Vector length (dimensions):", len(vector))
print("First 10 numbers of the vector:")
print(vector[:10])