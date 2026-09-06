from dotenv import load_dotenv
import os
from notion_client import Client

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))


def get_all_pages() -> list[dict]:
    response = notion.search(
        filter={"property": "object", "value": "page"}
    )

    results = []

    for page in response["results"]:
        page_id = page["id"]
        title = (
            page.get("properties", {})
            .get("title", {})
            .get("title", [{}])[0]
            .get("plain_text", "Untitled")
        )

        try:
            content = notion.blocks.children.list(block_id=page_id)

            if not content["results"]:
                print(f"⚠️ Empty page skipped: {title}")
                continue

            results.append({
                "page_id": page_id,
                "title": title,
                "blocks": content["results"]
            })

        except Exception as e:
            print(f"⚠️ Failed to fetch page {title}: {e}")
            continue

    return results


def get_database_entries(database_id: str) -> list[dict]:
    response = notion.search(
        filter={"property": "object", "value": "page"},
    )

    results = []

    for entry in response["results"]:
        # only get entries belonging to this database
        parent = entry.get("parent", {})
        if parent.get("database_id", "").replace("-", "") != database_id.replace("-", ""):
            continue

        entry_id = entry["id"]
        title = (
            entry.get("properties", {})
            .get("Name", {})
            .get("title", [{}])[0]
            .get("plain_text", "Untitled")
        )

        try:
            content = notion.blocks.children.list(block_id=entry_id)
            results.append({
                "page_id": entry_id,
                "title": title,
                "blocks": content["results"]
            })

        except Exception as e:
            print(f"⚠️ Failed to fetch entry {title}: {e}")
            continue

    return results