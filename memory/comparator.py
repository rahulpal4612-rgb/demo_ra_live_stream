import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "qwen/qwen3.8-27b"


def compare_memories(new_memory, existing_memory):

    prompt = f"""
You are a semantic memory comparator.

Compare a NEW memory with an EXISTING memory.

NEW MEMORY:
Type: {new_memory["type"]}
Content: {new_memory["content"]}

EXISTING MEMORY:
Type: {existing_memory["type"]}
Content: {existing_memory["content"]}

Classify their relationship as exactly ONE of:

DUPLICATE:
Both memories express the same underlying information.
Different wording alone does not make them different.

UPDATE:
Both memories refer to the same underlying fact, preference,
decision, or project information, but the new memory changes,
replaces, or meaningfully updates the existing memory.

NEW:
The memories represent different information.

Important:
- Compare meaning, not wording.
- If the new memory and existing memory express opposite,
  conflicting, or changed preferences, facts, or decisions,
  classify them as UPDATE, not DUPLICATE.
- A preference changing from detailed to concise, or concise to detailed,
  is an UPDATE.
- A decision changing from one technology/database to another
  is an UPDATE.
- DUPLICATE means the underlying information is genuinely the same,
  even if the wording is different.
- Similar topic or similar subject does NOT mean DUPLICATE.
- Do not invent information.
- Return ONLY valid JSON.

Return exactly:
{{"decision": "DUPLICATE"}}

or:
{{"decision": "UPDATE"}}

or:
{{"decision": "NEW"}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=20
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)

        if result.get("decision") in {"DUPLICATE", "UPDATE", "NEW"}:
            return result

    except json.JSONDecodeError:
        pass

    return {"decision": "NEW"}


if __name__ == "__main__":

    new_memory = {
        "type": "USER_PREFERENCE",
        "content": "User prefers simple explanations when learning technical concepts."
    }

    existing_memory = {
        "type": "USER_PREFERENCE",
        "content": "User likes technical concepts to be explained simply."
    }

    print(compare_memories(new_memory, existing_memory))