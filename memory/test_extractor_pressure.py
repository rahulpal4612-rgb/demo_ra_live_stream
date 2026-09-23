from memory.extractor import extract_memories


tests = [
    {
        "name": "Strong preference",
        "message": "I absolutely prefer simple explanations.",
        "expected_certainty": "high",
    },
    {
        "name": "Uncertain preference",
        "message": "I might prefer simpler explanations.",
        "expected_certainty": "low",
    },
    {
        "name": "Updated preference",
        "message": "I don't want simple explanations anymore. Give me detailed explanations.",
        "expected_certainty": "high",
    },
    {
        "name": "Considering PostgreSQL",
        "message": "I'm considering using PostgreSQL.",
        "expected_certainty": "low",
    },
    {
        "name": "Decided PostgreSQL",
        "message": "I've decided to use PostgreSQL.",
        "expected_certainty": "high",
    },
    {
        "name": "Conditional decision",
        "message": "If PostgreSQL works well, I'll probably use it.",
        "expected_certainty": "low",
    },
    {
        "name": "Undecided database",
        "message": "I haven't decided between SQLite and PostgreSQL.",
        "expected_certainty": None,
    },
    {
        "name": "Past versus current",
        "message": "I used MongoDB before, but I'm using SQLite now.",
        "expected_certainty": "high",
    },
    {
        "name": "Assistant is wrong",
        "message": "My assistant says I prefer Python, but that's wrong. I prefer C++.",
        "expected_certainty": "high",
    },
    {
        "name": "Preference with reason",
        "message": "I prefer C++ because I already know it well.",
        "expected_certainty": "high",
    },
    {
        "name": "Future possibility",
        "message": "Maybe I'll switch databases next month.",
        "expected_certainty": "low",
    },
    {
        "name": "Explicit remember",
        "message": "Remember this: I want simple explanations.",
        "expected_certainty": "high",
    },
    {
        "name": "General question",
        "message": "What is gradient descent?",
        "expected_certainty": None,
    },
    {
        "name": "Temporary information",
        "message": "I had coffee this morning.",
        "expected_certainty": None,
    },
    {
        "name": "Learning possibility",
        "message": "I'm thinking about learning Rust someday.",
        "expected_certainty": "low",
    },
    {
        "name": "Negative decision",
        "message": "I decided not to use PostgreSQL.",
        "expected_certainty": "high",
    },
    {
        "name": "Undecided SQLite",
        "message": "I could use SQLite, but I haven't made a decision.",
        "expected_certainty": None,
    },
    {
        "name": "Committed SQLite",
        "message": "I've decided to stick with SQLite, although PostgreSQL was tempting.",
        "expected_certainty": "high",
    },
]


for i, test in enumerate(tests, start=1):

    messages = [
        {
            "role": "user",
            "content": test["message"]
        }
    ]

    result = extract_memories(messages)

    memories = result.get("memories", [])

    if test["expected_certainty"] is None:
        passed = len(memories) == 0
    else:
        passed = any(
            memory.get("certainty") == test["expected_certainty"]
            for memory in memories
        )

    status = "PASS" if passed else "FAIL"

    print(f"TEST {i}: {test['name']}")
    print(f"USER: {test['message']}")
    print(f"EXPECTED CERTAINTY: {test['expected_certainty']}")
    print(f"RESULT: {result}")
    print(f"STATUS: {status}")
    print("-" * 60)