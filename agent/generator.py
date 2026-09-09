import os
from dotenv import load_dotenv
from groq import Groq
from ingestion.utils import count_tokens, TOKENIZER
import random

from agent.prompt import (
    SYSTEM_PROMPT,
    REACT_PROMPT,
    CONTEXT_PROMPT,
    NO_CONTEXT_PROMPT,
    NO_HISTORY_CONTEXT_PROMPT,
    NO_PERSONAL_CONTEXT_PROMPT,
    NO_WEB_CONTEXT_PROMPT
)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MAX_CONTEXT_TOKENS = 6428


def format_chunks(chunks: list[dict]) -> str:
    if not chunks:
        return "No context retrieved."

    formatted = []
    for i, chunk in enumerate(chunks):
        metadata = chunk.get("metadata", {})
        source_type = metadata.get("source_type", "unknown")
        source_path = metadata.get("source_path", "unknown")
        text = chunk.get("text", "")

        formatted.append(
            f"[{i+1}] source_type: {source_type} | source: {source_path}\n"
            f"    text: {text}"
        )

    return "\n\n".join(formatted)


def extract_sources(chunks: list[dict]) -> list[str]:
    if not chunks:
        return []

    sources = []
    seen = set()

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        source_type = metadata.get("source_type", "unknown")
        source_path = metadata.get("source_path", "unknown")

        source = f"{source_type} — {source_path}"

        if source not in seen:
            seen.add(source)
            sources.append(source)

    return [
        f"[{i+1}] {source}"
        for i, source in enumerate(sources)
    ]

def limit_chunks_by_tokens(
    chunks: list[dict],
    history: str,
    query: str,
    max_tokens: int
) -> list[dict]:
    if not chunks:
        return []

    selected = []

    for chunk in chunks:
        test_chunks = selected + [chunk]

        formatted = format_chunks(test_chunks)

        test_context = CONTEXT_PROMPT.format(
            chunks=formatted,
            history=history if history else "No previous conversation.",
            query=query
        )

        if count_tokens(test_context) > max_tokens:
            break

        selected.append(chunk)

    return selected


def generate(query: str, chunks: list[dict], history: str, action: str = "") -> dict:
    if action == "history":
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"""
Conversation history:
{history}

User's question:
{query}

Answer the user's question using the conversation history above.

If the history contains enough information, answer directly.
Do not say that you cannot answer if the information is present in the history.
If the history genuinely does not contain enough information, say so honestly.
"""
                }
            ],
            max_tokens=1000
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": []
        }

    if not chunks and action == "personal_not_found":
        return {"answer": NO_PERSONAL_CONTEXT_PROMPT, "sources": []}

    if not chunks and action == "web_not_found":
        return {"answer": NO_WEB_CONTEXT_PROMPT, "sources": []}

    if not chunks and action == "not_found":
        return {"answer": NO_CONTEXT_PROMPT, "sources": []}

    if not chunks:
        return {"answer": NO_CONTEXT_PROMPT, "sources": []}

    print(f"📦 Chunks before limiter: {len(chunks)}")
    print("\n🧪 CHUNKS ACTUALLY SENT TO GENERATOR:")
    for i, chunk in enumerate(chunks):
      print(f"\n[{i+1}] score={chunk.get('score')}")
      print(f"source={chunk.get('metadata', {}).get('source_path')}")
      print(chunk.get('text', '')[:1000])


    # Limit chunks only if the context becomes too large
    chunks = limit_chunks_by_tokens(
    chunks,
    history,
    query,
    MAX_CONTEXT_TOKENS
)
    print(f"📦 Chunks after limiter: {len(chunks)}")

    # format chunks
    formatted_chunks = format_chunks(chunks)
    print(f"📏 Formatted chunks characters: {len(formatted_chunks)}")

  

    filled_context = CONTEXT_PROMPT.format(
        chunks=formatted_chunks,
        history=history if history else "No previous conversation.",
        query=query
    )
    print(f"📏 Filled context characters: {len(filled_context)}")
    print(f"📏 Filled context tokens: {count_tokens(filled_context)}")
    print(f"📏 System prompt tokens: {count_tokens(SYSTEM_PROMPT + '\n' + REACT_PROMPT)}")

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + "\n" + REACT_PROMPT},
            {"role": "user", "content": filled_context}
        ],
        max_tokens=1000
    )

    answer = response.choices[0].message.content
    sources = extract_sources(chunks)

    return {"answer": answer, "sources": sources}

