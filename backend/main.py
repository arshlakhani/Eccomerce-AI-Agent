from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import ask_agent
app = FastAPI(
    title="Eccomerce AI Agent",
    description="AI-powered analytics for eccomerce data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class chatRequest(BaseModel):
    question: str
    thread_id: str = "default"

class chatResponse(BaseModel):
    message: str
    thread_id: str

@app.get("/")
def home():
    return {
        "message": "E-commerce AI Analyst API is running!"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

@app.post("/chat", response_model=chatResponse)
def chat(request: chatRequest):
    try:
        answer = ask_agent(
            question=request.question,
            thread_id=request.thread_id
        )

        return chatResponse(
            answer=answer,
            thread_id=request.thread_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )