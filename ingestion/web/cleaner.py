from bs4 import BeautifulSoup


def cleaner(contents: list[dict]) -> list[dict]:
  clean_texts = []
  for item in contents:
    url = item.get("url")
    html_text = item.get("html")
    try:
      soup = BeautifulSoup(html_text, "html.parser")
      for tag in soup(["script", "style", "nav", "footer", "header", "ads"]):
        tag.decompose()
      if "wikipedia.org" in url:
        content = soup.find(id="mw-content-text")
        if content:
          soup = content
        references = soup.find(id="References")
        if references:
          for element in references.find_all_next():
            element.decompose()
          references.decompose()
      text = soup.get_text(" ", strip=True)
      if not text.strip():
        print(f"⚠️ No text extracted from {url}")
        continue
      clean_texts.append({"url": url, "clean_text": text})
    except Exception as e:
      print(f"⚠️ Failed to clean {url}: {e}")
      continue
  return clean_texts
