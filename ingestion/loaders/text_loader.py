import re


def strip_extra_blank_lines(text: str) -> str:
    # collapse 3+ consecutive newlines down to a single blank line
    return re.sub(r'\n{3,}', '\n\n', text)


def strip_extra_spaces(text: str) -> str:
    # collapse runs of 2+ spaces/tabs into a single space
    return re.sub(r'[ \t]{2,}', ' ', text)


def strip_control_characters(text: str) -> str:
    # remove non-printable control chars, but keep \n and \t
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)


CLEANING_RULES = {
    "extra_blank_lines": strip_extra_blank_lines,
    "extra_spaces": strip_extra_spaces,
    "control_characters": strip_control_characters,
}


def TextLoader(document: dict) -> dict:
    path = document.get("file_path")
    ignore = document.get("ignore", [])

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # fall back to a lenient read rather than crashing on odd encodings
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    if not content.strip():
        raise ValueError(f"File is empty or near-empty: {path}")

    for rule in ("control_characters", "extra_blank_lines", "extra_spaces"):
        if rule in ignore:
            content = CLEANING_RULES[rule](content)

    return {
        "text": content,
        "source_path": path,
        "doc_type": "txt",
        "structure": None,
        "extraction_method": "plain_text",
    }