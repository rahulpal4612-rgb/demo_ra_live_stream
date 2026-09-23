from memory.database import add_memory, update_memory, get_all_memories,delete_memory
from memory.extractor import extract_memories
from memory.validator import validate_memory
from memory.retrieval import find_similar_memories
from memory.comparator import compare_memories

def save_extracted_memories(memories):
    for memory in memories:
        add_memory(
            memory["type"], 
            memory["content"], 
            memory["importance"], 
            "conversation", 
            1
        )

def is_duplicate(memory):
    candidates = find_similar_memories(memory["content"])
    for candidate in candidates:
        if candidate["type"] != memory["type"]:
            continue
        result = compare_memories(memory, candidate)
        if result["decision"] == "DUPLICATE":
            return True
    return False

def certainty_to_confirmed(certainty):
    if certainty == "high":
        return 1
    if certainty == "low":
        return 0
    return 0

def is_forget_request(messages):
    if not messages:
        return False

    # Find the latest user message
    for message in reversed(messages):
        if message["role"] == "user":
            content = message["content"].strip().lower()

            return (
                content == "forget"
                or content.startswith("forget ")
            )

    return False
    

def get_forget_text(messages):
    latest_message = messages[-1]
    content = latest_message["content"].strip()

    return content[6:].strip()

def find_memory_to_forget(messages):
    forget_text = get_forget_text(messages)

    candidates = find_similar_memories(forget_text, top_k=3)

    for candidate in candidates:
        if candidate["type"] not in [
            "USER_PREFERENCE",
            "PERSONAL_FACT",
            "PROJECT_CONTEXT",
            "PROJECT_PROGRESS",
            "DECISION",
            "LEARNING_PROGRESS"
        ]:
            continue

        comparison = compare_memories(
            {
                "type": candidate["type"],
                "content": forget_text
            },
            candidate
        )

        if comparison["decision"] == "DUPLICATE":
            return candidate["id"]

    return None

   
def process_memories(messages):
    if is_forget_request(messages):
     memory_id = find_memory_to_forget(messages)

     if memory_id is not None:
        delete_memory(memory_id)

     return {
        "memories": []
    }
    result = extract_memories(messages)
    print("EXTRACTED:", result)
    
    valid_memories = []
    for memory in result["memories"]:
        validation = validate_memory(messages, memory)
        if not validation["valid"]:
            continue
            
        print("VALID:", memory)
        candidates = find_similar_memories(memory["content"])
        print("CANDIDATES:", candidates)
        
        handled = False
        for candidate in candidates:
            if candidate["type"] != memory["type"]:
                continue
                
            comparison = compare_memories(memory, candidate)
            print("COMPARISON:", comparison)
            
            if comparison["decision"] == "DUPLICATE":
                handled = True
                break
                
            if comparison["decision"] == "UPDATE":
                # Mark the old memory as OUTDATED
                update_memory(
                    memory_id=candidate["id"],
                    type=candidate["type"],
                    content=candidate["content"],
                    importance=candidate["importance"],
                    source="conversation",
                    confirmed=0,
                    status="OUTDATED"
                )
                
                # Save the new memory as a new ACTIVE memory
                memory["confirmed"] = certainty_to_confirmed(memory["certainty"])
                add_memory(
                    type=memory["type"],
                    content=memory["content"],
                    importance=memory["importance"],
                    source="conversation",
                    confirmed=memory["confirmed"]
                )
                valid_memories.append(memory)
                handled = True
                break
                
        if handled:
            continue
            
        memory["confirmed"] = certainty_to_confirmed(memory["certainty"])
        add_memory(
            type=memory["type"],
            content=memory["content"],
            importance=memory["importance"],
            source="conversation",
            confirmed=memory["confirmed"]
        )
        valid_memories.append(memory)
        
    return {
        "memories": valid_memories
    }



