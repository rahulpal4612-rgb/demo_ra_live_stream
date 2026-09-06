import re
from collections import Counter

from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
import pikepdf


def check_scanned(path, sample_pages=3) -> bool:
    reader = PdfReader(path)
    pages_to_check = min(sample_pages, len(reader.pages))

    for i in range(pages_to_check):
        text = reader.pages[i].extract_text()
        if text and text.strip():
            return False   # found real text on this page -> not scanned

    return True   # no extractable text on any sampled page -> likely scanned


def strip_page_numbers(text: str) -> str:
    # lines that are just a number (optionally with dashes/brackets), on their own line
    return re.sub(r'(?m)^\s*[-\[\(]?\s*\d+\s*[-\]\)]?\s*$\n?', '', text)


def strip_watermarks(text: str, watermark_patterns=None) -> str:
    # generic pass: strip common watermark-style lines
    default_patterns = [r'(?im)^\s*(confidential|draft|sample|watermark)\s*$']
    patterns = watermark_patterns or default_patterns
    for pattern in patterns:
        text = re.sub(pattern, '', text)
    return text


def find_repeated_lines(pages_text: list, min_occurrence_ratio=0.5) -> set:
    # a line that appears near-identically on many pages is very likely a header/footer
    line_counts = Counter()
    for page_text in pages_text:
        lines = {line.strip() for line in page_text.split('\n') if line.strip()}
        line_counts.update(lines)

    threshold = max(2, int(len(pages_text) * min_occurrence_ratio))
    return {line for line, count in line_counts.items() if count >= threshold}


def strip_repeated_lines(pages_text: list, repeated_lines: set) -> list:
    cleaned = []
    for page_text in pages_text:
        lines = [line for line in page_text.split('\n') if line.strip() not in repeated_lines]
        cleaned.append('\n'.join(lines))
    return cleaned


CLEANING_RULES = {
    "page_numbers": strip_page_numbers,
    "watermarks": strip_watermarks,
}


def PDFLoader(document: dict) -> dict:
    path = document.get("file_path")
    ignore = document.get("ignore", [])
    reader = PdfReader(path)

    if reader.is_encrypted:
        raise ValueError(f"PDF is password-protected: {path}")

    try:
        with pikepdf.open(path) as pdf:
            pass  # structure parses cleanly -> not corrupted at a low level
    except pikepdf.PdfError as e:
        raise ValueError(f"PDF is corrupted at low level: {e}")

    if check_scanned(path):
        pages = convert_from_path(path, dpi=200)
        pages_text = [pytesseract.image_to_string(page_image) for page_image in pages]
        extraction_method = "ocr"

    else:
        pages_text = [(page.extract_text() or "") for page in reader.pages]
        extraction_method = "text_layer"

    # cross-page cleanup first, since header/footer detection needs the page list
    if "repeated_headers" in ignore or "repeated_footers" in ignore:
        repeated_lines = find_repeated_lines(pages_text)
        pages_text = strip_repeated_lines(pages_text, repeated_lines)

    content = "\n".join(pages_text)

    # single-pass regex cleanup on the joined text
    for rule in ("page_numbers", "watermarks"):
        if rule in ignore:
            content = CLEANING_RULES[rule](content)

    return {
        "text": content,
        "source_path": path,
        "doc_type": "pdf",
        "structure": None,
        "extraction_method": extraction_method,
    }