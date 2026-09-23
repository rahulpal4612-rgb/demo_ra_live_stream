import os
import json
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "qwen/qwen3.8-27b"


def validate_memory(messages, memory):
    conversation = "\n".join(
        f"{message['role'].upper()}: {message['content']}"
        for message in messages
    )

    prompt = f"""
You are a semantic validator for a long-term memory system.

Your job is to determine whether an extracted memory accurately represents
the information stated by the user in the conversation.

The memory should be accepted only if:

1. The memory is supported by the user's actual statements.
2. The memory preserves the user's meaning.
3. The memory type is appropriate.
4. The certainty correctly represents the user's level of commitment.
5. The memory does not contain invented information.

Important:
- Do not treat assistant statements as proof of user facts or preferences.
- If the user denies having said or expressed something, do not infer the opposite fact or preference from that denial.
- Do not accept a memory that changes uncertainty into certainty.
- Do not accept information that the user never stated.
- Judge the meaning of the complete user statement, not individual keywords.
- The extractor has already decided that the information is worth remembering.
- Your job is ONLY to check whether the extracted memory is semantically correct.

Return ONLY valid JSON in exactly this structure:

{{
    "valid": true
}}

or:

{{
    "valid": false
}}

Conversation:

{conversation}

Extracted memory:

{json.dumps(memory, indent=2)}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=100
    )

    content = response.choices[0].message.content

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return {"valid": False}

    if not isinstance(result, dict):
        return {"valid": False}

    if not isinstance(result.get("valid"), bool):
        return {"valid": False}

    return result