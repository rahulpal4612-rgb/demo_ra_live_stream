from sentence_transformers import SentenceTransformer
import time

embedding_model = SentenceTransformer('all-mpnet-base-v2')
BATCH_SIZE = 32


def encode_batch_with_retry(texts: list[str], delay=2, max_tries=3) -> list | None:
    for attempt in range(1, max_tries + 1):
        try:
            vectors = embedding_model.encode(texts, show_progress_bar=False)
            return vectors
        except Exception as e:
            print(f"⚠️ Attempt {attempt}/{max_tries} failed: {e}")
            if attempt < max_tries:
                sleep_time = delay * attempt
                print(f"🔄 Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                print("❌ Max retries reached. Batch skipped.")
                return None


def embedder(chunks: list[dict]) -> list[dict]:
    if not chunks:
        print("Nothing to embed.")
        return []

    failed_indices = []

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        for i, text in enumerate(texts):
            token_count = len(
                embedding_model.tokenizer.encode(
                    text, add_special_tokens=False
                )
            )

            if token_count > 512:
                print(f"🚨 OVERSIZED CHUNK: {token_count} tokens")
                print(f"Chunk index: {start + i}")
                print(f"Text preview: {text[:500]}")

        vectors = encode_batch_with_retry(texts)

        if vectors is None:
            failed_indices.extend(range(start, start + len(batch)))
            continue

        for i, chunk in enumerate(batch):
            chunk["embedding"] = vectors[i].tolist()

    if failed_indices:
        print(
            f"⚠️ {len(failed_indices)} chunks failed embedding: indices {failed_indices}"
        )

    return [c for c in chunks if "embedding" in c]
