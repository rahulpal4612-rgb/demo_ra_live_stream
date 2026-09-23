
from memory.database import get_all_memories
import numpy as np
from ingestion.embeding import embedding_model



ALWAYS_LOAD_RULES = {
    "USER_PREFERENCE": 2,
    "PROJECT_PROGRESS": 2,
    "DECISION": 3
}

def find_similar_memories(memory,top_k = 3):
    data = get_all_memories()
    result = []
    for d in data:
        if d[5]!= 1 and d[8] != "ACTIVE":
            continue

        existing_memory = d[2]
        score = similarity(existing_memory,memory)

        result.append({
              "id": d[0],
            "type": d[1],
            "content": existing_memory,
            "importance": d[3],
            "score": score
        })

    result.sort(key=lambda x: x["score"], reverse=True)

    return result


def similarity(query, memory):
    query_vector = embedding_model.encode([query])[0]
    memory_vector = embedding_model.encode([memory])[0]

    query_vector = query_vector / np.linalg.norm(query_vector)
    memory_vector = memory_vector / np.linalg.norm(memory_vector)

    return float(np.dot(query_vector, memory_vector))


def get_baseline_memories():
    data = get_all_memories()
    d = []

    for c in data:
        t = c[1]
        imp = c[3]
        content = c[2]
        confirmed = c[5]

        if t in ALWAYS_LOAD_RULES and confirmed == 1:
            if imp >= ALWAYS_LOAD_RULES[t]:
                d.append({
                    "type": t,
                    "content": content,
                    "importance": imp
                })

    return d

def get_relevant_memories(query, top_k=3):
    data = get_all_memories()
    results = []

    for d in data:

        if d[5] != 1 and d[8] != "ACTIVE":
            continue

        memory = d[2]
        score = similarity(query, memory)

        results.append({
            "type": d[1],
            "content": memory,
            "importance": d[3],
            "score": score
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:top_k]

def retrieve_memories(query, top_k=3):
    baseline = get_baseline_memories()
    relevant = get_relevant_memories(query, top_k)

    memories = baseline + relevant

    unique = {}

    for memory in memories:
        key = (memory["type"], memory["content"])
        unique[key] = memory

    memories = list(unique.values())

    return memories


# query = "What is the capital of France?"

# print(get_relevant_memories(query))

# print(get_relevant_memories("What choices have I made for my project?"))
# print(get_baseline_memories())


