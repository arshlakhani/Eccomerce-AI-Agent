
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import ask_agent

app = FastAPI(
    title="E-commerce AI Analyst API",
    description="AI-powered analytics for e-commerce data",
    version="1.0.0"
)

# Allow requests from the React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request format
class ChatRequest(BaseModel):
    question: str
    thread_id: str = "default"


# Response format
class ChatResponse(BaseModel):
    answer: str
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


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        answer = ask_agent(
            question=request.question,
            thread_id=request.thread_id
        )

        return ChatResponse(
            answer=answer,
            thread_id=request.thread_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


from sqlalchemy import text
from database import engine

@app.get("/analytics/summary")
def analytics_summary():
    try:
        query = text("""
            SELECT
                SUM("Revenue") AS total_revenue,
                SUM("Quantity") AS total_quantity,
                COUNT(DISTINCT "InvoiceNo") AS total_invoices,
                COUNT(DISTINCT "CustomerID") AS unique_customers,
                COUNT(DISTINCT "Country") AS total_countries
            FROM online_retail
            WHERE "Quantity" > 0
              AND "Revenue" > 0;
        """)

        with engine.connect() as connection:
            result = connection.execute(query).mappings().one()

        return {
            "total_revenue": float(result["total_revenue"]),
            "total_quantity": int(result["total_quantity"]),
            "total_invoices": int(result["total_invoices"]),
            "unique_customers": int(result["unique_customers"]),
            "total_countries": int(result["total_countries"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
