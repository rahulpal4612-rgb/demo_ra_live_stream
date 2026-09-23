from memory.validator import validate_memory


tests = [
    {
        "name": "Uncertainty changed to certainty",
        "messages": [
            {
                "role": "user",
                "content": "I'm thinking about switching from SQLite to PostgreSQL."
            }
        ],
        "memory": {
            "type": "DECISION",
            "content": "User decided to switch from SQLite to PostgreSQL.",
            "importance": 3,
            "certainty": "high"
        },
        "expected": False
    },

    {
        "name": "Correct uncertainty",
        "messages": [
            {
                "role": "user",
                "content": "I'm thinking about switching from SQLite to PostgreSQL."
            }
        ],
        "memory": {
            "type": "PROJECT_CONTEXT",
            "content": "User is considering switching from SQLite to PostgreSQL.",
            "importance": 2,
            "certainty": "low"
        },
        "expected": True
    },

    {
        "name": "Negation",
        "messages": [
            {
                "role": "user",
                "content": "I don't prefer complicated explanations."
            }
        ],
        "memory": {
            "type": "USER_PREFERENCE",
            "content": "User prefers complicated explanations.",
            "importance": 3,
            "certainty": "high"
        },
        "expected": False
    },

    {
        "name": "Assistant contradiction",
        "messages": [
            {
                "role": "user",
                "content": "I prefer simple explanations."
            },
            {
                "role": "assistant",
                "content": "Actually, you prefer detailed technical explanations."
            }
        ],
        "memory": {
            "type": "USER_PREFERENCE",
            "content": "User prefers detailed technical explanations.",
            "importance": 3,
            "certainty": "high"
        },
        "expected": False
    },

    {
        "name": "Invented reason",
        "messages": [
            {
                "role": "user",
                "content": "I decided to use SQLite."
            }
        ],
        "memory": {
            "type": "DECISION",
            "content": "User decided to use SQLite because PostgreSQL was too expensive.",
            "importance": 3,
            "certainty": "high"
        },
        "expected": False
    },

    {
        "name": "Correct paraphrase",
        "messages": [
            {
                "role": "user",
                "content": "From now on, please explain things in very simple language."
            }
        ],
        "memory": {
            "type": "USER_PREFERENCE",
            "content": "User prefers simple explanations.",
            "importance": 3,
            "certainty": "high"
        },
        "expected": True
    },

    {
        "name": "Wrong memory type",
        "messages": [
            {
                "role": "user",
                "content": "I'm currently working on Layer 5."
            }
        ],
        "memory": {
            "type": "USER_PREFERENCE",
            "content": "User prefers working on Layer 5.",
            "importance": 2,
            "certainty": "high"
        },
        "expected": False
    },

    {
        "name": "Past versus current",
        "messages": [
            {
                "role": "user",
                "content": "I used PostgreSQL before, but now I'm using SQLite."
            }
        ],
        "memory": {
            "type": "PROJECT_CONTEXT",
            "content": "User is currently using SQLite.",
            "importance": 2,
            "certainty": "high"
        },
        "expected": True
    },

    {
        "name": "Conditional decision",
        "messages": [
            {
                "role": "user",
                "content": "If SQLite becomes a problem, I may switch to PostgreSQL."
            }
        ],
        "memory": {
            "type": "DECISION",
            "content": "User decided to switch to PostgreSQL.",
            "importance": 3,
            "certainty": "high"
        },
        "expected": False
    },

    {
        "name": "Mixed uncertainty and confirmed fact",
        "messages": [
            {
                "role": "user",
                "content": "I haven't decided whether to use PostgreSQL, but I'm currently using SQLite."
            }
        ],
        "memory": {
            "type": "PROJECT_CONTEXT",
            "content": "User is currently using SQLite.",
            "importance": 2,
            "certainty": "high"
        },
        "expected": True
    }
]


for i, test in enumerate(tests, start=1):
    result = validate_memory(
        test["messages"],
        test["memory"]
    )

    actual = result.get("valid")

    status = "PASS" if actual == test["expected"] else "FAIL"

    print(f"TEST {i}: {test['name']}")
    print(f"Expected: {test['expected']}")
    print(f"Actual:   {actual}")
    print(f"Result:   {status}")
    print()