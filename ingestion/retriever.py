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
    index, metadata_list, texts_list = load_store()

    print("\n🔎 PERSONAL STORE DEBUG")
    print("FAISS vectors:", index.ntotal)
    print("Metadata:", len(metadata_list))
    print("Texts:", len(texts_list))

    for i, metadata in enumerate(metadata_list):
        if metadata.get("source_type") == "notion":
            print(
                "NOTION FOUND:",
                i,
                metadata.get("source_path"),
                "| text:",
                texts_list[i][:200]
            )
    results = search(query_vector[0].tolist(), top_k=500)
    print("\n🔎 RESULTS RETURNED BY STORE.SEARCH")

    for r in results[:20]:
     print(
        "score:", r.get("score"),
        "| index/source:",
        r.get("metadata", {}).get("source_type"),
        "| text:",
        r.get("text", "")[:100]
    )

     
    print("\n🔎 CHECKING IF RAG WAS RETRIEVED")

    for r in results:
      text = r.get("text", "").lower()

      if "rag stands for retrieval" in text:
        print("🎯 RAG CHUNK RETRIEVED!")
        print("Score:", r.get("score"))
        print("Source:", r.get("metadata", {}).get("source_type"))
        print("Text:", r.get("text"))

    # print("\n🔍 DEBUG PERSONAL RESULTS")

    # for r in results:
    #     print(
    #         "score:", r.get("score"),
    #         "| source_type:", r.get("metadata", {}).get("source_type"),
    #         "| doc_type:", r.get("metadata", {}).get("doc_type"),
    #         "| text:", r.get("text", "")[:300]
    #     )

    personal_results = []

    for r in results:
        source = r.get("metadata", {}).get("source_type", "personal_doc")

        if source != "web":
            r["source"] = source
            personal_results.append(r)

    personal_results.sort(key=lambda x: x["score"], reverse=True)

    return personal_results[:TOP_K]

def search_web_only(query: str) -> list[dict]:
    query_vector = embed_query(query)

    # Search more candidates because the store contains
    # both personal and web documents
    results = search(query_vector[0].tolist(), top_k=50)

    # Keep only web documents
    web_results = []

    for r in results:
        source = r.get("metadata", {}).get("source_type", "personal_doc")

        if source == "web":
            r["source"] = source
            web_results.append(r)
            print("\nDEBUG WEB RESULT")
            print("Source path:", r.get("metadata", {}).get("source_path"))
            print("Doc ID:", r.get("metadata", {}).get("doc_id"))

    # Keep the best web results
    web_results.sort(key=lambda x: x["score"], reverse=True)

    return web_results[:TOP_K]


def retrieve(query: str) -> list[dict]:
    query_vector = embed_query(query)
    personal_results = search(query_vector[0].tolist(), top_k=TOP_K)

    # remove hardcoded threshold — return personal results first
    # agent's is_relevant() will judge if they're good enough
    if personal_results:
        return personal_results

    # only go to web if no results at all
    print("⚠️ No personal results — triggering web search.")
    web_pipeline(query)
    all_results = search(query_vector[0].tolist(), top_k=TOP_K)

    for r in all_results:
        r["source"] = r.get("metadata", {}).get("source_type", "personal_doc")

    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:TOP_K]

