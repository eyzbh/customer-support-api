
from enum import Enum

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from database import create_tables, get_connection
from sentiment_service import analyze_sentiment
from ticket_analyzer import analyze_ticket
app = FastAPI(
    title="Customer Support API",
    description="An API for managing customer support tickets.",
    version="1.0.0",
)

create_tables()


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TicketStatus(str, Enum):
    open = "open"
    closed = "closed"


class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(min_length=5, max_length=150)
    description: str = Field(min_length=10, max_length=2000)
    priority: Priority = Priority.medium


class TicketUpdate(BaseModel):
    status: TicketStatus

class SentimentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
class TicketAnalysisRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)

@app.get("/")
def home():
    return {
        "message": "Welcome to the Customer Support API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}



@app.post(
    "/sentiment",
    summary="Analyze text sentiment",
    description=(
        "Classify text as positive, neutral, or negative "
        "using a pretrained Transformer model. "
        "Returns the predicted sentiment and its confidence score."
    ),
    response_description="The predicted sentiment and score.",
    responses={
        503: {
            "description": (
                "Sentiment analysis is temporarily unavailable "
                "because model inference failed."
            )
        }
    },
)

def predict_sentiment(request: SentimentRequest):
    try:
        result = analyze_sentiment(request.text)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sentiment analysis is temporarily unavailable.",
        )

    return {
        "text": request.text,
        "sentiment": result["sentiment"],
        "score": result["score"],
    }


@app.post(
    "/analyze-ticket",
    responses={
        503: {
            "description": "The local AI model is temporarily unavailable."
        }
    },
)
def analyze_support_ticket(request: TicketAnalysisRequest):
    try:
        result = analyze_ticket(request.message)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ticket analysis is temporarily unavailable.",
        )

    return result
@app.post("/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: TicketCreate):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO tickets (
                customer_name, email, subject,
                description, priority, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ticket.customer_name,
                str(ticket.email),
                ticket.subject,
                ticket.description,
                ticket.priority.value,
                TicketStatus.open.value,
            ),
        )

        row = connection.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        return dict(row)


@app.get("/tickets")
def get_tickets():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM tickets ORDER BY id"
        ).fetchall()

        return [dict(row) for row in rows]


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )

        return dict(row)


@app.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: int, update: TicketUpdate):
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE tickets SET status = ? WHERE id = ?",
            (update.status.value, ticket_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )

        row = connection.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        return dict(row)
