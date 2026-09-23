from ingestion.embeding import embedding_model
import numpy as np

memory = "User decided to use SQLite for their project."
query = "What database am I using?"

memory_vector = embedding_model.encode([memory])[0]
query_vector = embedding_model.encode([query])[0]

memory_vector = memory_vector / np.linalg.norm(memory_vector)
query_vector = query_vector / np.linalg.norm(query_vector)

similarity = np.dot(query_vector, memory_vector)

print("Similarity:", similarity)