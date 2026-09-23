from memory.pipeline import process_memories
import sqlite3

messages = [
    {
        "role": "user",
        "content": "I am currently learning Rust for backend development."
    }
]

print(process_memories(messages))

print(process_memories(messages))

result = process_memories(messages)

print("\nPIPELINE RESULT:")
print(result)

conn = sqlite3.connect("memory.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT id, type, content, importance, confirmed, status
    FROM memory
    WHERE content LIKE '%backend%'
""")

print("\nDATABASE RESULT:")
for row in cursor.fetchall():
    print(row)

conn.close()