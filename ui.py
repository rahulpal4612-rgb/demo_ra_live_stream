import streamlit as st
import requests
import os
from ingestion.pipeline import ingest_document

st.title("🧠 Personal AI Assistant")

uploaded_file = st.file_uploader(
    "📎 Upload a document",
    type=["pdf"]
)

if uploaded_file is not None:
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"Uploaded: {uploaded_file.name}")

    if st.button("Process document"):
        ingest_document(file_path)
        st.success("Document processed successfully!")

# Create UI chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input at bottom
message = st.chat_input("Ask anything...")

if message:

    # Show/store user message
    st.session_state.messages.append({
        "role": "user",
        "content": message
    })

    with st.chat_message("user"):
        st.write(message)

    # Send message to FastAPI
    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"message": message}
    )

    result = response.json()

    # Show/store assistant response
    st.session_state.messages.append({
    "role": "assistant",
    "content": result["answer"],
    "sources": result.get("sources", [])
})

    with st.chat_message("assistant"):
     st.write(result["answer"])

     sources = result.get("sources", [])

     if sources:
        with st.expander("📚 Sources"):
            for source in sources:
                st.write(source)