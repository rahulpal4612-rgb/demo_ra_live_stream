from ingestion.embeding import embedding_model
from ingestion.store import search
import faiss, numpy as np

query = "what is this document about"
vec = embedding_model.encode([query])[0].tolist()
results = search(vec, top_k=3)

for r in results:
    print(r["score"], r["text"][:200])
    print()