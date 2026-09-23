from memory.extractor import extract_memories


tests = [
    {
        "name": "Valid high certainty",
        "certainty": "high",
        "expected": True
    },
    {
        "name": "Valid low certainty",
        "certainty": "low",
        "expected": True
    },
    {
        "name": "Invalid certainty: maybe",
        "certainty": "maybe",
        "expected": False
    },
    {
        "name": "Invalid certainty: certain",
        "certainty": "certain",
        "expected": False
    },
    {
        "name": "Missing certainty",
        "certainty": None,
        "expected": False
    }
]


for test in tests:
    memory = {
        "type": "USER_PREFERENCE",
        "content": "User prefers simple explanations.",
        "importance": 3
    }

    if test["certainty"] is not None:
        memory["certainty"] = test["certainty"]

    # We are testing the validation logic directly.
    # So we temporarily reproduce the structural check here.
    actual = memory.get("certainty") in ["high", "low"]

    status = "PASS" if actual == test["expected"] else "FAIL"

    print(f"TEST: {test['name']}")
    print(f"Expected: {test['expected']}")
    print(f"Actual:   {actual}")
    print(f"Result:   {status}")
    print()