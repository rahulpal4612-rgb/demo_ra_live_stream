from dotenv import load_dotenv
import os
from tavily import TavilyClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

tavily = TavilyClient(api_key=TAVILY_API_KEY)

def search(query: str, depth: str = "basic") -> list[dict]:
    response = tavily.search(query=query, max_results=3, search_depth=depth)
    print("\n🔎 TAVILY RESULTS")
    print("\n🧪 TAVILY SCORES:")
    for r in response["results"]:
     print(r["title"], "→", r["score"])

    for r in response["results"]:
     print("\nURL:", r["url"])
     print("SNIPPET:", r["content"][:500])

    results = []
    for r in response["results"]:
        results.append({
            "url": r["url"],
            "snippet": r["content"]
        })

    return results


