from memory.pipeline import certainty_to_confirmed


tests = [
    ("high", 1),
    ("low", 0),
    ("maybe", 0),
    (None, 0),
]


for certainty, expected in tests:
    actual = certainty_to_confirmed(certainty)

    status = "PASS" if actual == expected else "FAIL"

    print(f"certainty: {certainty}")
    print(f"expected:  {expected}")
    print(f"actual:    {actual}")
    print(f"result:    {status}")
    print("-" * 40)