import re
from ingestion.utils import count_tokens, TOKENIZER
from docling.chunking import HybridChunker

CHUNK_SIZE = 300       # test
CHUNK_OVERLAP = 30
MIN_CHUNK_SIZE = 50


def count_tokens(text: str) -> int:
    return len(TOKENIZER.encode(text, add_special_tokens=False))


def split_by_tokens(text: str, chunk_size: int, overlap: int) -> list[str]:
    tokens = TOKENIZER.encode(text, add_special_tokens=False)
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]

        chunk_text = TOKENIZER.decode(
            chunk_tokens,
            skip_special_tokens=True
        )

        chunks.append(chunk_text)

        if end == len(tokens):
            break

        start += chunk_size - overlap

    return chunks


def normalize_item(item, document):
    label = str(item.label)

    if label == "table":
        dataframe = item.export_to_dataframe(document)
        text = dataframe.to_string(index=False)

    elif label == "picture":
        text = item.caption_text(document) or ""

    else:
        text = item.text or ""

    page = item.prov[0].page_no if item.prov else None

    return {
        "label": label,
        "text": text,
        "page": page,
    }


def merge_small_chunks(chunks: list[str], min_tokens: int) -> list[str]:
    merged = []
    buffer = ""

    for i, chunk in enumerate(chunks):

        if buffer:
            combined = buffer + " " + chunk
        else:
            combined = chunk

        if count_tokens(combined) < min_tokens and i < len(chunks) - 1:
            buffer = combined
        else:
            merged.append(combined)
            buffer = ""

    if buffer:
        if merged:
            merged[-1] = merged[-1] + " " + buffer
        else:
            merged.append(buffer)

    return merged


def split_by_structure(text: str, structure: list) -> list[dict]:
    """
    Uses heading positions to split markdown into sections first,
    then token-splits each section.
    Returns chunks with section title attached.
    """

    if not structure:
        return []

    heading_pattern = re.compile(r'(?m)^(#{1,6})\s+(.*)$')
    matches = list(heading_pattern.finditer(text))

    if not matches:
        return []

    sections = []

    for i, match in enumerate(matches):
        section_start = match.start()

        if i + 1 < len(matches):
            section_end = matches[i + 1].start()
        else:
            section_end = len(text)

        section_text = text[section_start:section_end].strip()
        section_title = match.group(2).strip()
        section_level = len(match.group(1))

        sections.append({
            "title": section_title,
            "level": section_level,
            "text": section_text,
        })

    raw_chunks = []

    for section in sections:
        if count_tokens(section["text"]) <= CHUNK_SIZE:
           sub_chunks = [section["text"]]
        else:
         sub_chunks = split_by_tokens(
        section["text"],
        CHUNK_SIZE,
        CHUNK_OVERLAP
    )

        for chunk_text in sub_chunks:
            raw_chunks.append({
                "text": chunk_text,
                "section_title": section["title"],
                "section_level": section["level"],
            })

    return raw_chunks


def chunk_document(document: dict) -> list[dict]:

    source_path = document.get("source_path", "")
    doc_type = document.get("doc_type", "")
    extraction_method = document.get("extraction_method", "")

    # PDF → Docling → HybridChunker
    if doc_type == "pdf":

        docling_document = document.get("docling_document")

        if docling_document is None:
            raise ValueError(
                f"PDF has no DoclingDocument: {source_path}"
            )

        chunker = HybridChunker()
        hybrid_chunks = list(chunker.chunk(docling_document))

        # Test: print first 10 chunks
        for i, chunk in enumerate(hybrid_chunks[:10]):
            print(f"\n--- CHUNK {i} ---")
            print("TEXT:", chunk.text[:200])
            print("HEADINGS:", chunk.meta.headings)

            pages = set()

            for item in chunk.meta.doc_items:
                for prov in item.prov:
                    pages.add(prov.page_no)

            print("PAGES:", sorted(pages))

        if not hybrid_chunks:
            raise ValueError(
                f"HybridChunker produced no chunks: {source_path}"
            )

        chunks = []

        for i, chunk in enumerate(hybrid_chunks):

            chunk_text = chunk.text.strip()

            if not chunk_text:
                continue

            headings = chunk.meta.headings
            section_title = headings[-1] if headings else None

            pages = set()

            for item in chunk.meta.doc_items:
                for prov in item.prov:
                    pages.add(prov.page_no)

            pages = sorted(pages)

            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "source_path": source_path,
                    "doc_type": doc_type,
                    "extraction_method": extraction_method,
                    "chunk_index": i,
                    "total_chunks": len(hybrid_chunks),
                    "section_title": section_title,
                    "section_level": None,
                    "pages": pages,
                    "token_count": count_tokens(chunk_text),
                }
            })

        return chunks

    # Existing Markdown / text behavior
    text = document.get("text", "")
    structure = document.get("structure")

    if not text or not text.strip():
        raise ValueError(
            f"Document has no text to chunk: {source_path}"
        )

    if structure and doc_type == "md":

        raw_chunks = split_by_structure(text, structure)

        texts = [c["text"] for c in raw_chunks]
        section_titles = [c["section_title"] for c in raw_chunks]
        section_levels = [c["section_level"] for c in raw_chunks]

    else:

        texts = split_by_tokens(
            text,
            CHUNK_SIZE,
            CHUNK_OVERLAP
        )

        section_titles = [None] * len(texts)
        section_levels = [None] * len(texts)

    # texts = merge_small_chunks(
    #     texts,
    #     MIN_CHUNK_SIZE
    # )

    diff = len(texts) - len(section_titles)

    if diff > 0:
        section_titles += [None] * diff
        section_levels += [None] * diff

    else:
        section_titles = section_titles[:len(texts)]
        section_levels = section_levels[:len(texts)]

    chunks = []

    for i, chunk_text in enumerate(texts):

        chunks.append({
            "text": chunk_text,
            "metadata": {
                "source_path": source_path,
                "doc_type": doc_type,
                "extraction_method": extraction_method,
                "chunk_index": i,
                "total_chunks": len(texts),
                "section_title": section_titles[i],
                "section_level": section_levels[i],
                "token_count": count_tokens(chunk_text),
            }
        })

    return chunks