import os
import hashlib
from loaders.base import get_loader
from chunker import chunk_document
from embeding import embedder
from metadata import create_metadata
from store import upsert_chunks, load_store

FAILURES_LOG = "failures.log"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def hash_file(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def log_failure(file_path: str, reason: str):
    with open(FAILURES_LOG, "a") as f:
        f.write(f"{file_path} | {reason}\n")
    print(f"❌ Failed: {file_path} — {reason}")


def already_indexed(doc_id: str, content_hash: str, metadata_list: list) -> bool:
    for m in metadata_list:
        if m.get("doc_id") == doc_id and m.get("content_hash") == content_hash:
            return True
    return False


# ─── Single file ──────────────────────────────────────────────────────────────

def ingest_document(file_path: str):
    try:
        loader, document = get_loader(file_path)
        if loader is None:
            log_failure(file_path, "Unsupported file type")
            return
        document = loader(document)  # ✅ called here with config
    except Exception as e:
        log_failure(file_path, f"Loader failed: {e}")
        return

    if not document.get("text", "").strip():
        log_failure(file_path, "Empty text after loading")
        return

    try:
        chunks = chunk_document(document)
    except Exception as e:
        log_failure(file_path, f"Chunker failed: {e}")
        return

    if not chunks:
        log_failure(file_path, "No chunks produced")
        return

    try:
        embedded_chunks = embedder(chunks)
    except Exception as e:
        log_failure(file_path, f"Embedder failed: {e}")
        return

    if not embedded_chunks:
        log_failure(file_path, "No chunks survived embedding")
        return

    try:
        for chunk in embedded_chunks:
            chunk["metadata"] = create_metadata(chunk, document)
    except Exception as e:
        log_failure(file_path, f"Metadata failed: {e}")
        return

    try:
        upsert_chunks(embedded_chunks)
    except Exception as e:
        log_failure(file_path, f"Store upsert failed: {e}")
        return

    print(f"✅ Ingested: {file_path} ({len(embedded_chunks)} chunks)")

# ─── Folder ───────────────────────────────────────────────────────────────────

def ingest_folder(folder_path: str):
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return

    # load current store state once — used for skip checks
    _, metadata_list, _ = load_store()

    all_files = []
    for root, _, files in os.walk(folder_path):
        for fname in files:
            all_files.append(os.path.join(root, fname))

    print(f"📂 Found {len(all_files)} files in {folder_path}")

    skipped = 0
    ingested = 0
    failed = 0

    for file_path in all_files:
        try:
            content_hash = hash_file(file_path)
            doc_id = hashlib.sha256(file_path.encode()).hexdigest()

            if already_indexed(doc_id, content_hash, metadata_list):
                print(f"⏭️  Skipped (unchanged): {file_path}")
                skipped += 1
                continue

            ingest_document(file_path)
            ingested += 1

        except Exception as e:
            log_failure(file_path, f"Unexpected error: {e}")
            failed += 1

    print(f"\n📊 Done — ingested: {ingested} | skipped: {skipped} | failed: {failed}")
    if failed:
        print(f"⚠️  See {FAILURES_LOG} for details.")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <file_or_folder_path>")
    else:
        path = sys.argv[1]
        if os.path.isdir(path):
            ingest_folder(path)
        elif os.path.isfile(path):
            ingest_document(path)
        else:
            print(f"❌ Path not found: {path}")