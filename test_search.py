from sentence_transformers import CrossEncoder

model = CrossEncoder("BAAI/bge-reranker-base")

print("Reranker loaded successfully")