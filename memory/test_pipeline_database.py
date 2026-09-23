import memory.pipeline as pipeline
from memory.pipeline import process_memories
from memory.database import get_all_memories


messages = [
    {
        "role": "user",
        "content": "I am currently learning Docker."
    }
]


fake_memories = {
    "memories": [
        {
            "type": "USER_PREFERENCE",
            "content": "User prefers simple explanations.",
            "importance": 3,
            "certainty": "high"
        },
        {
            "type": "DECISION",
            "content": "User decided to use SQLite because PostgreSQL was too expensive.",
            "importance": 3,
            "certainty": "high"
        }
    ]
}


def fake_extract_memories(messages):
    return fake_memories


pipeline.extract_memories = fake_extract_memories


result = process_memories(messages)

print("PIPELINE RESULT:")
print(result)

print("\nDATABASE:")
print(get_all_memories())