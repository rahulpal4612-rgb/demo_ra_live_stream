
import os
import json
import numpy as np
import faiss
from datetime import datetime

STORE_DIR = "store"
FAISS_PATH = os.path.join(STORE_DIR, "index.faiss")
METADATA_PATH = os.path.join(STORE_DIR, "metadata.json")
TEXTS_PATH = os.path.join(STORE_DIR, "texts.json")

EMBEDDING_DIM = 768  # all-mpnet-base-v2 output dimension


# ─── Load / Save ──────────────────────────────────────────────────────────────

def load_store() -> tuple[faiss.Index, list, list]:
    os.makedirs(STORE_DIR, exist_ok=True)

    if os.path.exists(FAISS_PATH):
        index = faiss.read_index(FAISS_PATH)
    else:
        index = faiss.IndexFlatIP(EMBEDDING_DIM)

    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r") as f:
            metadata_list = json.load(f)
    else:
        metadata_list = []

    if os.path.exists(TEXTS_PATH):
        with open(TEXTS_PATH, "r") as f:
            texts_list = json.load(f)
    else:
        texts_list = []

    return index, metadata_list, texts_list


def save_store(index: faiss.Index, metadata_list: list, texts_list: list):
    os.makedirs(STORE_DIR, exist_ok=True)

    faiss.write_index(index, FAISS_PATH)

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata_list, f, indent=2)

    with open(TEXTS_PATH, "w") as f:
        json.dump(texts_list, f, indent=2)


# ─── Delete ───────────────────────────────────────────────────────────────────

def delete_by_doc_id(
    doc_id: str,
    index: faiss.Index,
    metadata_list: list,
    texts_list: list
) -> tuple[faiss.Index, list, list]:
    """
    FAISS doesn't support deletion natively.
    Rebuild index from scratch, skipping chunks that belong to doc_id.
    """
    keep_indices = [
        i for i, m in enumerate(metadata_list)
        if m.get("doc_id") != doc_id
    ]

    new_index = faiss.IndexFlatIP(EMBEDDING_DIM)
    new_metadata = []
    new_texts = []

    if keep_indices:
        # reconstruct vectors from old index for kept chunks
        all_vectors = np.zeros(
            (index.ntotal, EMBEDDING_DIM),
            dtype=np.float32
        )

        for i in range(index.ntotal):
            all_vectors[i] = faiss.rev_swig_ptr(
                index.get_xb(),
                index.ntotal * EMBEDDING_DIM
            )[i * EMBEDDING_DIM:(i + 1) * EMBEDDING_DIM]

        kept_vectors = np.array(
            [all_vectors[i] for i in keep_indices],
            dtype=np.float32
        )

        new_index.add(kept_vectors)
        new_metadata = [metadata_list[i] for i in keep_indices]
        new_texts = [texts_list[i] for i in keep_indices]

    return new_index, new_metadata, new_texts


# ─── Upsert ───────────────────────────────────────────────────────────────────

def upsert_chunks(chunks: list[dict]):
    """
    Main write operation.
    Each chunk must have: text, embedding (list of 768 floats), metadata (dict with chunk_id, doc_id etc.)
    """
    index, metadata_list, texts_list = load_store()

    # group incoming chunks by doc_id — delete old entries for any doc being re-ingested
    doc_ids_seen = set(chunk["metadata"]["doc_id"] for chunk in chunks)

    for doc_id in doc_ids_seen:
        existing_ids = {m.get("doc_id") for m in metadata_list}

        if doc_id in existing_ids:
            print(
                f"🔄 Re-ingesting doc_id {doc_id[:8]}... deleting old chunks."
            )

            index, metadata_list, texts_list = delete_by_doc_id(
                doc_id,
                index,
                metadata_list,
                texts_list
            )

    # add new chunks
    vectors = []

    for chunk in chunks:
        embedding = chunk.get("embedding")
        text = chunk.get("text", "")
        metadata = chunk.get("metadata", {})

        if embedding is None:
            print(
                f"⚠️ Chunk missing embedding, skipping: "
                f"{metadata.get('chunk_id', 'unknown')}"
            )
            continue

        vectors.append(embedding)
        metadata_list.append(metadata)
        texts_list.append(text)

    if vectors:
        vectors_np = np.array(vectors, dtype=np.float32)

        # normalize for cosine similarity via inner product
        faiss.normalize_L2(vectors_np)
        index.add(vectors_np)

    save_store(index, metadata_list, texts_list)

    print(
        f"✅ Upserted {len(vectors)} chunks into store. "
        f"Total: {index.ntotal}"
    )


# ─── Search ───────────────────────────────────────────────────────────────────

def search(
    query_vector: list,
    top_k: int = 5,
    source_paths: list[str] | None = None
) -> list[dict]:
    index, metadata_list, texts_list = load_store()

    if index.ntotal == 0:
        print("⚠️ Store is empty.")
        return []

    query_np = np.array([query_vector], dtype=np.float32)
    faiss.normalize_L2(query_np)

    # Search more candidates so expired chunks can be filtered out
    if source_paths:
     candidate_k = index.ntotal
    else:
     candidate_k = min(index.ntotal, top_k * 10)
    scores, indices = index.search(query_np, candidate_k)

    results = []
    now = datetime.now()

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        metadata = metadata_list[idx]
        if source_paths and metadata.get("source_path") not in source_paths:
            continue

        # Ignore expired web documents
        if metadata.get("source_type") == "web":
            expires_at = metadata.get("expires_at")

            if expires_at:
                try:
                    expiry_time = datetime.fromisoformat(expires_at)

                    if expiry_time < now:
                        continue

                except ValueError:
                    pass

        results.append({
            "text": texts_list[idx],
            "metadata": metadata,
            "score": float(score)
        })

        if len(results) == top_k:
            break

    return results
