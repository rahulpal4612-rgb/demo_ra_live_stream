from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

MAX_MESSAGES = 10
SUMMARY_KEEP = 4  # keep last 4 messages after summarization


class Memory:
    def __init__(self):
        self.memory = []
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def is_empty(self) -> bool:
        return len(self.memory) == 0

    def add_message(self, role: str, content: str):
        self.memory.append({
            "role": role,
            "content": content
        })

    def get_history(self) -> list[dict]:
        return self.memory

    def get_history_as_text(self) -> str:
        history = []
        for msg in self.memory:
            history.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(history)

    def clear(self):
        self.memory = []

    def _summarize(self, messages_to_summarize: list[dict]) -> str:
        # build text of messages to summarize
        text = "\n".join(
            f"{m['role']}: {m['content']}"
            for m in messages_to_summarize
        )

        response = self.client.chat.completions.create(
           model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this conversation history concisely, preserving key facts, topics discussed, and important context:\n\n{text}"
                }
            ],
            max_tokens=300
        )

        return response.choices[0].message.content

    def summarize_if_needed(self):
        if len(self.memory) < MAX_MESSAGES:
            return  # nothing to do

        print("📝 History too long — summarizing older messages...")

        # split: old messages to summarize, recent to keep
        messages_to_summarize = self.memory[:-SUMMARY_KEEP]
        recent_messages = self.memory[-SUMMARY_KEEP:]

        # summarize old messages
        summary_text = self._summarize(messages_to_summarize)

        # replace history with summary + recent
        self.memory = [
            {"role": "assistant", "content": f"Summary of earlier conversation: {summary_text}"}
        ] + recent_messages

        print("✅ History summarized successfully.")