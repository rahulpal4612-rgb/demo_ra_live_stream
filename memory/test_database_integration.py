from memory.database import add_memory, get_all_memories


memory = {
    "type": "DECISION",
    "content": "User decided to use SQLite.",
    "importance": 2,
    "source": "conversation",
    "confirmed": 1
}


add_memory(
    type=memory["type"],
    content=memory["content"],
    importance=memory["importance"],
    source=memory["source"],
    confirmed=memory["confirmed"]
)


print("DATABASE:")
print(get_all_memories())