from transformers import AutoTokenizer

MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)


def count_tokens(text: str) -> int:
    return len(TOKENIZER.encode(text, add_special_tokens=False))