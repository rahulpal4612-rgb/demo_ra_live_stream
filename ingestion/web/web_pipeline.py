from datetime import datetime, timedelta
from ingestion.web.searcher import search
from ingestion.web.fetcher import fetch
from ingestion.web.cleaner import cleaner
from ingestion.chunker import chunk_document
from ingestion.embeding import embedder
from ingestion.metadata import create_metadata
from ingestion.store import upsert_chunks


TTL_HOURS = 24


def build_web_document(url: str, clean_text: str) -> dict:
    return {
        "text": clean_text,
        "source_path": url,
        "doc_type": "web",
        "extraction_method": "tavily+beautifulsoup",
        "structure": None,
        "expires_at": (datetime.now() + timedelta(hours=TTL_HOURS)).isoformat()
    }


def web_pipeline(query: str) -> list[str]:
    ingested_urls = []

    # 1. search
    print("DEBUG: BEFORE SEARCH")
    search_results = search(query)
    if not search_results:
        print("⚠️ No search results returned.")
        return []

    # 2. fetch
    print("DEBUG: BEFORE FETCH")
    urls = [r["url"] for r in search_results]
    fetched = fetch(urls)
    if not fetched:
        print("⚠️ No pages fetched.")
        return []

    # 3. clean
    print("DEBUG: BEFORE FETCH")
    cleaned = cleaner(fetched)
    if not cleaned:
        print("⚠️ No pages cleaned.")
        return []

    # 4. chunk → embed → metadata → store per page
    for page in cleaned:
        url = page.get("url")
        clean_text = page.get("clean_text")

        try:
            # build document
            document = build_web_document(url, clean_text)

            # chunk
            print("DEBUG: BEFORE CHUNK")
            chunks = chunk_document(document)
            if not chunks:
                print(f"⚠️ No chunks produced for {url}")
                continue

            # embed
            print("DEBUG: BEFORE EMBED")
            embedded_chunks = embedder(chunks)
            if not embedded_chunks:
                print(f"⚠️ No chunks embedded for {url}")
                continue

            # attach metadata
            for chunk in embedded_chunks:
                chunk["metadata"] = create_metadata(chunk, document)
                chunk["metadata"]["source_type"] = "web"
                chunk["metadata"]["expires_at"] = document["expires_at"]

            # upsert
            upsert_chunks(embedded_chunks)
            ingested_urls.append(url)
            print(f"✅ Ingested web page: {url}")

        except Exception as e:
            print(f"⚠️ Failed to ingest {url}: {e}")
            continue

    return ingested_urls