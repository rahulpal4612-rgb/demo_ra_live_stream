from base import get_loader

# point these at real files you actually have
test_files = [
    "C:/Users/BST/Desktop/sample.md",
    "C:/Users/BST/Desktop/sample.pdf",
    "C:/Users/BST/Desktop/sample.txt.txt",
    "C:/Users/BST/Desktop/nonexistent.xyz",     # should hit the "unsupported type" path
]

for filepath in test_files:
    print(f"\n--- Testing: {filepath} ---")
    result = get_loader(filepath)

    if result is None:
        print("  -> Returned None (check failures.log for reason)")
        continue

    print(f"  doc_type: {result['doc_type']}")
    print(f"  extraction_method: {result.get('extraction_method')}")
    print(f"  text length: {len(result['text'])} chars")
    print(f"  structure: {result.get('structure')}")
    print(f"  first 200 chars:\n  {result['text'][:200]!r}")

print("\n--- failures.log contents ---")
try:
    with open("failures.log") as f:
        print(f.read())
except FileNotFoundError:
    print("(no failures logged)")