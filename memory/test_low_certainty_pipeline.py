import memory.pipeline as pipeline
from memory.pipeline import process_memories
from memory.database import get_all_memories


messages = [
    {
        "role": "user",
        "content": "I'm considering switching to PostgreSQL."
    }
]


fake_memories = {
    "memories": [
        {
            "type": "PROJECT_CONTEXT",
            "content": "User is considering switching to PostgreSQL.",
            "importance": 2,
            "certainty": "low"
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