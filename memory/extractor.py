import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "qwen/qwen3.8-27b"

def extract_memories(messages: list[dict]) -> dict:
    conversation = "\n".join(
        f"{message['role'].upper()}: {message['content']}"
        for message in messages
    )

    prompt = f"""
You are a long-term memory extractor for a personal AI assistant.

Your job is to identify information from the conversation that would
be useful for the assistant to remember across future conversations.

Save information only when it has durable future value.

Save things such as:
- stable user preferences
- important personal facts explicitly stated by the user
- important project context
- project progress
- important decisions
- learning progress
- preferences about how the assistant should behave

Do NOT save:
- ordinary questions
- temporary information with no future value
- general knowledge
- information about other people
- trivial details
- information that would not improve future conversations

Important:
- Do not invent facts about the user.
- Personal facts and user preferences must be supported by an explicit user statement.
- Never create a personal fact or preference solely because the assistant said, assumed, inferred, or claimed it.
- Assistant messages may provide context for decisions, project progress, or conclusions, but they cannot independently establish a user's personal facts or preferences.
- One memory must contain one atomic piece of information.

Importance rules:
- Assign importance using ONLY the integers 1, 2, or 3.
- 1 = Low importance. Small future value.
- 2 = Medium importance. Useful in future conversations.
- 3 = High importance. Very valuable for future conversations.
- NEVER output 0, 4, 5, or any other number.
- Do NOT use a 1-5 scale.

Certainty rules:
- Assign certainty using ONLY "high" or "low".
- "high" means the user explicitly states a fact, preference, decision,
  or committed project status as true/current.
- "low" means the user is considering, suggesting, exploring, or expressing
  a possibility without committing to it.
- If the user explicitly says they have not decided something, do not save
  the undecided possibility as a confirmed decision.
- However, save other parts of the statement if they contain durable,
  useful information.
- Judge the meaning of the complete user statement, not individual keywords.
- A possibility mentioned earlier in a sentence can be overridden by a
  later explicit commitment.
- Do not determine certainty from assistant messages alone.
- Certainty and importance are independent.
- A low-certainty memory can still be useful and should be saved when it
  has durable future value.
- Do not discard a memory merely because its certainty is low.

Allowed memory types:
USER_PREFERENCE
PERSONAL_FACT
PROJECT_CONTEXT
PROJECT_PROGRESS
DECISION
LEARNING_PROGRESS

Return ONLY valid JSON in exactly this structure:

{{
    "memories": [
        {{
            "type": "USER_PREFERENCE",
            "content": "User prefers very simple explanations.",
            "importance": 3,
            "certainty": "high"
        }}
    ]
}}

If there is nothing worth remembering, return:

{{
    "memories": []
}}

Conversation:

{conversation}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1000
    )

    content = response.choices[0].message.content

    try:
      result = json.loads(content)
    except json.JSONDecodeError:
      return {"memories": []}

    if not isinstance(result.get("memories"), list):
      return {"memories": []}


    allowed_types = {
    "USER_PREFERENCE",
    "PERSONAL_FACT",
    "PROJECT_CONTEXT",
    "PROJECT_PROGRESS",
    "DECISION",
    "LEARNING_PROGRESS"
}

    valid_memories = []

    for memory in result.get("memories", []):
      if not isinstance(memory, dict):
        continue

      if memory.get("type") not in allowed_types:
         continue

      content = memory.get("content")

      if not isinstance(content, str) or not content.strip():
          continue
      
      importance = memory.get("importance")


      if not isinstance(importance, int) or importance < 1 or importance > 3:
        continue

      if memory.get("certainty") not in ["high", "low"]:
        continue

      valid_memories.append(memory)

    result["memories"] = valid_memories

    return result