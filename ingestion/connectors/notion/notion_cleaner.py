SUPPORTED_TYPES = [
    "paragraph", "heading_1", "heading_2", "heading_3",
    "bulleted_list_item", "numbered_list_item",
    "to_do", "quote", "code"
]


def notion_cleaner(result: list[dict]) -> list[dict]:
    results = []

    for r in result:
        page_texts = []
        title = r["title"]
        page_id = r["page_id"]

        for block in r["blocks"]:
            block_type = block["type"]

            if block_type not in SUPPORTED_TYPES:
                continue

            rich_text = block[block_type].get("rich_text", [])
            if not rich_text:
                continue

            clean_text = rich_text[0]["plain_text"]
            if not clean_text:
                continue

            page_texts.append(clean_text)

        if not page_texts:
            print(f"⚠️ No text extracted from page: {title}")
            continue

        results.append({
            "page_id": page_id,
            "title": title,
            "text": "\n".join(page_texts)
        })

    return results