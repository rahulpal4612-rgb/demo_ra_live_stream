import os
from dotenv import load_dotenv
from groq import Groq
from agent.memory import Memory
from agent.generator import generate
from ingestion.retriever import retrieve, search_personal_only,search_web_only
from ingestion.web.web_pipeline import web_pipeline

load_dotenv()

memory = Memory()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def is_relevant(query: str, chunks: list[dict]) -> bool:
    """
    Let LLM decide if retrieved chunks actually answer the query.
    No hardcoded threshold — model judges relevance semantically.
    """
    if not chunks:
        return False

    # format top 3 chunks for LLM to evaluate
    formatted = "\n\n".join([
        f"[{i+1}] {c.get('text', '')[:300]}"
        for i, c in enumerate(chunks[:5])
    ])
    print("\n🔎 CHUNKS SENT TO RELEVANCE MODEL")

    for i, c in enumerate(chunks[:5]):
     print(
        f"[{i+1}] score={c.get('score')} "
        f"source={c.get('metadata', {}).get('source_type')} "
        f"text={c.get('text', '')[:500]}"
    )

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{
            "role": "user",
            "content": f"""User asked: "{query}"

Retrieved chunks:
{formatted}

Do these chunks contain enough relevant information to answer the user's question?
Reply with ONLY: YES or NO"""
        }],
        max_tokens=5
    )

    answer = response.choices[0].message.content.strip().upper()
    print(f"🧠 Relevance model returned: {repr(answer)}")
    return answer == "YES"


def build_contextualized_query(query: str, history: str) -> str:
    """
    Why: when user says "tell me more about that" the retriever
    doesn't know what "that" means. We ask Groq to rewrite the
    query with full context so retriever gets a meaningful search term.
    """
    if not history:
        return query

    response = client.chat.completions.create(
       model="qwen/qwen3.8-27b",
        messages=[{
            "role": "user",
            "content": f"""Given this conversation history:
{history}

The user just asked: "{query}"

Rewrite the user's question as a fully self-contained search query that includes all necessary context from the history. Return only the rewritten query, nothing else."""
        }],
        max_tokens=100
    )

    rewritten = response.choices[0].message.content.strip()
    return rewritten if rewritten else query

def is_followup(query: str, history: str) -> bool:
    """
    Stage 1 — Is this a follow-up to the conversation history?
    """
    if not history:
        return False

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{
            "role": "user",
            "content": f"""Conversation history:
{history}

User just asked: "{query}"

Is this question a follow-up to the conversation history above?

A follow-up question:
- References something mentioned earlier ("it", "that", "they", "more about", "tell me more")
- Continues the same topic from history
- Is a clarification of something already discussed

A NEW question:
- Introduces a completely new topic not mentioned in history
- Asks about something unrelated to the conversation so far
- Is a standalone question that makes sense without the history

Reply with ONLY: YES or NO"""
        }],
        max_tokens=5
    )

    answer = response.choices[0].message.content.strip().upper()
    return answer == "YES"


def can_history_answer(query: str, history: str) -> bool:
    """
    Stage 2A — Can the conversation history fully answer this question?
    """

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{
            "role": "user",
            "content": f"""Conversation history:
{history}

User just asked:
"{query}"

Decide whether the conversation history ALONE contains enough information
to give the user a complete and useful answer.

Important rules:

- If the user asks "tell me more", "give me more information",
  "explain more", or similar broad follow-up, answer YES only if
  the history contains substantial information that can satisfy
  that request.
- Having only one or two facts about the topic is NOT enough.
- If answering properly would require additional factual information,
  answer NO.
- Do not assume information that is not explicitly present in the history.

Reply with ONLY:
YES
or
NO"""
        }],
        max_tokens=5
    )

    answer = response.choices[0].message.content.strip().upper()
    return answer == "YES"


def route_new_query(query: str, history: str) -> str:
    """
    Stage 2B — Route a new query to the correct source.
    """
    response = client.chat.completions.create(
       model="qwen/qwen3.8-27b",
        messages=[{
            "role": "user",
            "content": f"""You are a query router for a personal knowledge assistant.

User asked: "{query}"

Classify this query into exactly one category:

SEARCH_PERSONAL — if the query:
- Contains ownership words: "my notes", "my books", "my ideas", "my documents", "my notion", "what did I write", "what do I have"
- Is asking about the user's own personal knowledge base
- Is NOT asking about current events or live data

SEARCH_WEB — if the query:
- Asks about current events, news, prices, latest versions, today, recent happenings
- Needs live or up-to-date information
- Is a factual question about the world that doesn't involve personal docs

SEARCH_BOTH — if the query:
- Needs both personal knowledge AND external information
- Is complex and could benefit from multiple sources
- Mixes personal context with general knowledge

Reply with ONLY one of these exact words:
SEARCH_PERSONAL
SEARCH_WEB
SEARCH_BOTH"""
        }],
        max_tokens=10
    )

    action = response.choices[0].message.content.strip()
    valid = ["SEARCH_PERSONAL", "SEARCH_WEB", "SEARCH_BOTH"]
    return action if action in valid else "SEARCH_BOTH"


def decide_action(query: str, history: str, contextualized_query: str = None) -> str:
    """
    Decide whether this is:
    - an answer from history
    - a personal search
    - a web search
    - a combined search

    Original query → used to detect follow-up.
    Contextualized query → used for routing.
    """

    # No history at all
    if not history:
        if any(word in query.lower() for word in ["that", "it", "they", "more about", "tell me more"]):
            return "CLARIFY"

        return route_new_query(query, history)

    # Stage 1 — detect follow-up using original question
    followup = is_followup(query, history)
    print(f"🔗 Is follow-up: {followup}")

    if followup:

        # Stage 2A — can history answer it?
        can_answer = can_history_answer(query, history)
        print(f"📖 Can history answer: {can_answer}")

        if can_answer:
            return "ANSWER_FROM_HISTORY"

        # History isn't enough → route contextualized query
        return route_new_query(contextualized_query or query, history)

    # New question → route normally
    return route_new_query(query, history)

def run(query: str) -> dict:
    history = memory.get_history_as_text()

    # 2. Decide action using previous history
    contextualized_query = build_contextualized_query(query, history)
    print(f"🔎 Searching for: {contextualized_query}")

# 3. Decide action
# Original query is used for follow-up detection.
# Contextualized query is used for routing.
    action = decide_action(query, history, contextualized_query)
    print(f"🧠 Action: {action}")

# 4. Add current user question to memory
    memory.add_message("user", query)

# 5. Summarize if history is too long
    memory.summarize_if_needed()

    # 6. handle CLARIFY
    if action == "CLARIFY":
        result = {
            "answer": "Could you clarify what you're referring to? I don't have enough context to understand your question.",
            "sources": []
        }
        memory.add_message("assistant", result["answer"])
        print(f"\n💬 Answer:\n{result['answer']}\n")
        return result


    # 7. route based on action
    if action == "ANSWER_FROM_HISTORY":
        print("💭 Answering from conversation history...")
        chunks = []
        result = generate(query, chunks, history, action="history")

    elif action == "SEARCH_PERSONAL":
        print("📚 Searching personal docs and Notion...")
        chunks = search_personal_only(contextualized_query)
        if not is_relevant(contextualized_query, chunks):
            print("⚠️ Nothing relevant found in personal docs.")
            result = generate(query, [], history, action="personal_not_found")
        else:
            result = generate(query, chunks, history)

    elif action == "SEARCH_WEB":
        print("🌐 Searching web...")
        web_pipeline(contextualized_query)
        chunks = search_web_only(contextualized_query)
        print(f"🔎 Retrieved {len(chunks)} web chunks")

        for i, chunk in enumerate(chunks[:5]):
           print(f"\n--- Web Chunk {i+1} ---")
           print(f"Score: {chunk.get('score')}")
           print(f"Source: {chunk.get('source')}")
           print(chunk.get('text', '')[:500])
        if not is_relevant(contextualized_query, chunks):
            result = generate(query, [], history, action="web_not_found")
        else:
            result = generate(query, chunks, history)

    else:  # SEARCH_BOTH
        print("🔍 Searching all sources...")
        chunks = retrieve(contextualized_query)
        if not is_relevant(contextualized_query, chunks):
            result = generate(query, [], history, action="not_found")
        else:
            result = generate(query, chunks, history)

    # 8. add answer to memory
    memory.add_message("assistant", result["answer"])

    # 9. print answer + sources
    print("\n💬 Answer:")
    print(result["answer"])

    if result["sources"]:
        print("\n📚 Sources:")
        for source in result["sources"]:
            print(f"   {source}")

    print()
    return result


if __name__ == "__main__":
    print("🤖 Personal Knowledge Assistant ready. Type 'exit' to quit.\n")

    while True:
        query = input("You: ").strip()

        if not query:
            continue

        if query.lower() in ["exit", "quit"]:
            print("👋 Ending session.")
            memory.clear()
            break

        run(query)