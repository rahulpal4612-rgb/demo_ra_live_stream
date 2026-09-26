from rank_bm25 import BM25Okapi
import re


def tokenize(text: str) -> list[str]:
    return re.findall(r'\d{2}-\d{2}-\d{4}|[a-zA-Z]+|\d+(?:\.\d+)?', text.lower())


def build_bm25(texts: list[str]):
    tokenized_texts = [
    tokenize(text)
    for text in texts
]

    return BM25Okapi(tokenized_texts)


def search_bm25(
    bm25,
    query: str,
    texts: list[str],
    metadata: list[dict],
    top_k: int = 5
) -> list[dict]:

    query_tokens = tokenize(query)

    scores = bm25.get_scores(query_tokens)

    ranked_indices = scores.argsort()[::-1][:top_k]

    results = []

    for idx in ranked_indices:
        results.append({
            "text": texts[idx],
            "metadata": metadata[idx],
            "score": float(scores[idx])
        })

    return results