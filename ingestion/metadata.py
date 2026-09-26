import hashlib
from datetime import datetime
from ingestion.utils import count_tokens


def create_hash(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def create_metadata(chunk: dict, document: dict) -> dict:

    chunk_meta = chunk.get("metadata", {})
    source_path = document.get("source_path")
    chunk_index = chunk_meta.get("chunk_index")

    # Unique ID for this particular chunk
    chunk_id = create_hash(
        source_path + str(chunk_index)
    )

    # Same ID for all chunks belonging to the same document
    doc_id = create_hash(source_path)

    metadata = {
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "source_path": source_path,
        "doc_type": document.get("doc_type"),
        "extraction_method": document.get("extraction_method"),
        "chunk_index": chunk_index,
        "total_chunks": chunk_meta.get("total_chunks"),
        "section_title": chunk_meta.get("section_title"),
        "section_level": chunk_meta.get("section_level"),
        "token_count": count_tokens(chunk.get("text", "")),
        "ingestion_timestamp": datetime.now().isoformat(),
        "content_hash": create_hash(chunk.get("text", "")),
        "pages": chunk_meta.get("pages", []),
    }

    return metadata