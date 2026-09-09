
import numpy as np
import faiss
from ingestion.embeding import embedding_model
from ingestion.store import search, load_store
from ingestion.web.web_pipeline import web_pipeline

CONFIDENCE_THRESHOLD = 0.5
TOP_K = 5


def embed_query(query: str) -> np.ndarray:
    vector = embedding_model.encode([query])[0]
    query_np = np.array([vector], dtype=np.float32)
    faiss.normalize_L2(query_np)
    return query_np


def search_personal_only(query: str) -> list[dict]:
    query_vector = embed_query(query)

    results = search(query_vector[0].tolist(), top_k=500)

    personal_results = []

    for r in results:
        source = r.get("metadata", {}).get("source_type", "personal_doc")

        if source != "web":
            r["source"] = source
            personal_results.append(r)

    personal_results.sort(key=lambda x: x["score"], reverse=True)

    return personal_results[:TOP_K]

def search_web_only(
    query: str,
    source_paths: list[str] | None = None
) -> list[dict]:
    
    query_vector = embed_query(query)

    results = search(
    query_vector[0].tolist(),
    top_k=50,
    source_paths=source_paths
)
    web_results = []

    for r in results:
        source = r.get("metadata", {}).get("source_type", "personal_doc")

        if source == "web":
            r["source"] = source
            web_results.append(r)

    web_results.sort(key=lambda x: x["score"], reverse=True)

    return web_results[:22]


def retrieve(query: str) -> list[dict]:
    query_vector = embed_query(query)
    personal_results = search_personal_only(query)
    # Return personal results first
    # agent's is_relevant() will judge if they're good enough
    if personal_results:
        return personal_results

    # Only go to web if no personal results exist
    print("⚠️ No personal results — triggering web search.")
    web_pipeline(query)

    all_results = search(query_vector[0].tolist(), top_k=TOP_K)

    for r in all_results:
        r["source"] = r.get("metadata", {}).get("source_type", "personal_doc")

    all_results.sort(key=lambda x: x["score"], reverse=True)

    return all_results[:TOP_K]
