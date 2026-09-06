import re


def strip_html_comments(text: str) -> str:
    return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)


def strip_badges(text: str) -> str:
    # markdown badge images, e.g. [![build](url)](url) or ![badge](url)
    text = re.sub(r'\[!\[.*?\]\(.*?\)\]\(.*?\)', '', text)   # linked badge
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)               # plain image (also catches badges)
    return text


def strip_navigation_links(text: str) -> str:
    # common nav patterns: lines that are just a row of links separated by | or -
    return re.sub(r'(?m)^\s*(\[.*?\]\(.*?\)\s*[\|\-]\s*)+\[.*?\]\(.*?\)\s*$\n?', '', text)


def strip_decorative_images(text: str) -> str:
    # any remaining standalone image syntax not caught as a badge
    return re.sub(r'!\[.*?\]\(.*?\)', '', text)


def strip_extra_blank_lines(text: str) -> str:
    return re.sub(r'\n{3,}', '\n\n', text)


CLEANING_RULES = {
    "html_comments": strip_html_comments,
    "badges": strip_badges,
    "navigation_links": strip_navigation_links,
    "decorative_images": strip_decorative_images,
    "extra_blank_lines": strip_extra_blank_lines,
}

# order matters: comments/badges/nav before the generic image stripper,
# so badges are removed via their own (more specific) rule first
RULE_ORDER = ["html_comments", "badges", "navigation_links", "decorative_images", "extra_blank_lines"]


def extract_structure(text: str) -> list:
    # capture heading hierarchy: [(level, heading_text), ...]
    headings = re.findall(r'(?m)^(#{1,6})\s+(.*)$', text)
    return [{"level": len(hashes), "title": title.strip()} for hashes, title in headings]


def MarkdownLoader(document: dict) -> dict:
    path = document.get("file_path")
    ignore = document.get("ignore", [])

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    if not content.strip():
        raise ValueError(f"File is empty or near-empty: {path}")

    # capture structure BEFORE cleaning, since strip_decorative_images etc.
    # don't touch headings, but it's safer to extract structure from the raw text
    structure = extract_structure(content)

    for rule in RULE_ORDER:
        if rule in ignore:
            content = CLEANING_RULES[rule](content)

    return {
        "text": content,
        "source_path": path,
        "doc_type": "md",
        "structure": structure,
        "extraction_method": "markdown",
    }