from ingestion.connectors.notion.notion_cleaner import notion_cleaner
from ingestion.connectors.notion.notion_fetcher import get_all_pages, get_database_entries
from ingestion.chunker import chunk_document
from ingestion.embeding import embedder
from ingestion.metadata import create_metadata
from ingestion.store import upsert_chunks
from datetime import datetime, timedelta
import os

TTL_HOURS = 24


def build_notion_document(title: str, page_id: str, text: str) -> dict:
    return {
        "text": text,
        "source_path": page_id,
        "doc_type": "notion",
        "extraction_method": "notion_api",
        "structure": None,
        "title": title,
        "expires_at": (datetime.now() + timedelta(hours=TTL_HOURS)).isoformat()
    }


def _ingest_cleaned(cleaned: list[dict], ingested_pages: list):
    for page in cleaned:
        title = page.get("title")
        page_id = page.get("page_id")
        clean_text = page.get("text")

        try:
            document = build_notion_document(title, page_id, clean_text)

            chunks = chunk_document(document)
            if not chunks:
                print(f"⚠️ No chunks produced for {title}")
                continue

            embedded_chunks = embedder(chunks)
            if not embedded_chunks:
                print(f"⚠️ No chunks embedded for {title}")
                continue

            for chunk in embedded_chunks:
                chunk["metadata"] = create_metadata(chunk, document)
                chunk["metadata"]["source_type"] = "notion"
                chunk["metadata"]["expires_at"] = document["expires_at"]

            upsert_chunks(embedded_chunks)
            ingested_pages.append(title)
            print(f"✅ Ingested Notion page: {title}")

        except Exception as e:
            print(f"⚠️ Failed to ingest {title}: {e}")
            continue


def notion_pipeline():
    ingested_pages = []

    # ── pages ──
    print(" Fetching Notion pages...")
    res = get_all_pages()
    if not res:
        print("⚠️ No pages found in Notion workspace.")
    else:
        cleaned = notion_cleaner(res)
        _ingest_cleaned(cleaned, ingested_pages)

    # ── database entries ──
    database_id = os.getenv("NOTION_DATABASE_ID")
    if not database_id:
        print("⚠️ NOTION_DATABASE_ID not set in .env — skipping database sync.")
    else:
        print("🗄️ Fetching Notion database entries...")
        db_res = get_database_entries(database_id)
        if not db_res:
            print("⚠️ No database entries found.")
        else:
            db_cleaned = notion_cleaner(db_res)
            _ingest_cleaned(db_cleaned, ingested_pages)

    return ingested_pages

if __name__ == "__main__":
    notion_pipeline()