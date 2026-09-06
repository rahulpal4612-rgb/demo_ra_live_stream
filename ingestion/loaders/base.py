from pathlib import Path
from datetime import datetime

from .pdf_loader import PDFLoader
from .markdown_loader import MarkdownLoader
from .text_loader import TextLoader


LOADER_REGISTRY = {
    ".pdf": PDFLoader,
    ".txt": TextLoader,
    ".md": MarkdownLoader,
}

IGNORE_RULES = {
    ".pdf": ["page_numbers", "repeated_headers", "repeated_footers", "watermarks"],
    ".txt": ["extra_blank_lines", "extra_spaces", "control_characters"],
    ".md": ["html_comments", "badges", "navigation_links", "decorative_images", "extra_blank_lines"],
}

FAILURE_LOG_PATH = "failures.log"


def get_ext(path: str) -> str:
    return Path(path).suffix.lower()


def log_failure(file_path: str, reason: str):
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"[{timestamp}] SKIPPED: {file_path} | reason: {reason}\n"
    with open(FAILURE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def build_document_config(file_path: str, ext: str) -> dict:
    document = {
        "file_path": file_path,
        "type_doc": ext,
        "ignore": IGNORE_RULES.get(ext, []),
        "type_loader": LOADER_REGISTRY.get(ext).__name__,
    }
    return document


def get_loader(file_path: str):
    ext = get_ext(file_path)
    loader_class = LOADER_REGISTRY.get(ext)

    if loader_class is None:
        log_failure(file_path, reason=f"unsupported file type: '{ext}'")
        return None, None

    document = build_document_config(file_path, ext)
    return loader_class, document