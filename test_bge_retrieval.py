import json
import faiss
from sentence_transformers import SentenceTransformer

from ingestion.bm25 import build_bm25, search_bm25, tokenize
from ingestion.fusion import reciprocal_rank_fusion


QUERY = "What was the withdrawal amount on 14-04-2025?"

# Load BGE store
with open("store_bge/texts.json", "r", encoding="utf-8") as f:
    texts = json.load(f)

with open("store_bge/metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

index = faiss.read_index("store_bge/index.faiss")

# Load BGE-M3
model = SentenceTransformer("BAAI/bge-m3")

# -----------------------------
# 1. BGE-M3 retrieval
# -----------------------------

query_embedding = model.encode(
    [QUERY],
    convert_to_numpy=True
).astype("float32")

faiss.normalize_L2(query_embedding)

scores, indices = index.search(
    query_embedding,
    len(texts)
)

faiss_results = []

for score, idx in zip(scores[0], indices[0]):
    faiss_results.append({
        "text": texts[idx],
        "metadata": metadata[idx],
        "score": float(score)
    })


# -----------------------------
# 2. BM25 retrieval
# -----------------------------

bm25 = build_bm25(texts)

bm25_results = search_bm25(
    bm25,
    QUERY,
    texts,
    metadata,
    top_k=20
)


# -----------------------------
# 3. RRF
# -----------------------------

fused_results = reciprocal_rank_fusion(
    [
        faiss_results,
        bm25_results
    ]
)


# -----------------------------
# 4. Print results
# -----------------------------

print("\nBGE-M3 + BM25 + RRF\n")

for rank, result in enumerate(fused_results[:10], start=1):
    print(
        f"Rank {rank}: "
        f"chunk {result['metadata']['chunk_index']} | "
        f"fusion score {result['fusion_score']:.6f}"
    )