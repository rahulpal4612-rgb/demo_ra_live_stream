from ingestion.connectors.notion.notion_pipeline import notion_pipeline


def connector_pipeline():
    print("🔄 Starting connector sync...\n")

    # ── Notion ──
    print("📓 Syncing Notion...")
    notion_results = notion_pipeline()

    if notion_results:
        print(f"✅ Notion synced {len(notion_results)} pages:")
        for title in notion_results:
            print(f"   - {title}")
    else:
        print("⚠️ No Notion pages ingested.")

    # ── Summary ──
    total = len(notion_results) if notion_results else 0
    print(f"\n📊 Sync complete — total ingested: {total}")

    return {
        "notion": notion_results or []
    }


if __name__ == "__main__":
    connector_pipeline()