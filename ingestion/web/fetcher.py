import requests
import validators

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html",
    "Accept-Language": "en-US,en;q=0.9"
}


def valid_syntax(url: str) -> bool:
    return bool(validators.url(url))


def fetch(urls: list[str]) -> list[dict]:
    contents = []

    for url in urls:
        if not valid_syntax(url):
            print(f" Invalid URL skipped: {url}")
            continue

        try:
            response = requests.get(url, timeout=10, headers=HEADERS)
            if "wikipedia.org" in url:
               with open("wikipedia_debug.html", "w", encoding="utf-8") as f:
                 f.write(response.text)

            if response.status_code != 200:
                print(f" Failed to fetch {url}: status {response.status_code}")
                continue

            content_type = response.headers.get("Content-Type", "").lower()

            if "text/html" not in content_type:
                print(f" Skipping non-HTML content: {url} ({content_type})")
                continue
            
            contents.append({
                "url": url,
                "html": response.text
            })

        except Exception as e:
            print(f" Error fetching {url}: {e}")
            continue

    return contents