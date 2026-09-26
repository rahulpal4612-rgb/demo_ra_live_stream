from fastapi import FastAPI
from pydantic import BaseModel
from agent.agent import run

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {"message": "Personal AI Assistant API is running"}


@app.post("/chat")
def chat(request: ChatRequest):
    result = run(request.message)
    return result