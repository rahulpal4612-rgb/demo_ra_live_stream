
import sqlite3
from datetime import datetime


def init_db():
    file = "memory.db"

    try:
        conn = sqlite3.connect(file)
        cursor = conn.cursor()

        print("Database memory.db is formed")

        # Create the table if it does not already exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance INTEGER NOT NULL,
                source TEXT NOT NULL,
                confirmed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(type, content)
            )
        """)

        # Check existing columns
        cursor.execute("PRAGMA table_info(memory)")
        columns = [row[1] for row in cursor.fetchall()]

        print("Columns before migration:", columns)

        # Add status if it does not exist
        if "status" not in columns:
            cursor.execute("""
                ALTER TABLE memory
                ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE'
            """)

            print("Added status column")
        else:
            print("Status column already exists")

        conn.commit()

        # Check the final schema
        cursor.execute("PRAGMA table_info(memory)")
        columns = cursor.fetchall()

        print("Final table schema:")
        for column in columns:
            print(column)

        conn.close()

        print("Database initialization completed")

    except Exception as e:
        print(f"Database is not formed. Error: {e}")


def add_memory(type, content, importance, source, confirmed=0,status="ACTIVE"):
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    current_time = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO memory
        (type, content, importance, source, confirmed, created_at, updated_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?,?)

        ON CONFLICT (type, content)
        DO UPDATE SET
            importance = excluded.importance,
            source = excluded.source,
            confirmed = excluded.confirmed,
            updated_at = excluded.updated_at
        """,
        (
            type,
            content,
            importance,
            source,
            confirmed,
            current_time,
            current_time,
            status
        )
    )

    conn.commit()
    conn.close()

def get_all_memories():
    conn = sqlite3.connect("memory.db")

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM memory")

    rows = cursor.fetchall()

    conn.close()

    return rows

def delete_memory(memory_id):
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM memory WHERE id = ?",
        (memory_id,)
    )

    conn.commit()
    conn.close()

def update_memory(memory_id, type, content, importance, source, confirmed=0, status="ACTIVE"):
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    current_time = datetime.now().isoformat()

    cursor.execute(
        """
        UPDATE memory
        SET type = ?,
            content = ?,
            importance = ?,
            source = ?,
            confirmed = ?,
            status = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            type,
            content,
            importance,
            source,
            confirmed,
            status,
            current_time,
            memory_id
        )
    )

    conn.commit()
    conn.close()


print(get_all_memories())











