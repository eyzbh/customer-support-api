
from enum import Enum
import logging
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    status,
)
from auth import require_api_key, require_reviewer
from pydantic import BaseModel, EmailStr, Field

from database import create_tables, get_connection
from sentiment_service import analyze_sentiment
from ticket_analyzer import analyze_ticket
from rag_service import answer_question
from persistent_approval_service import (
    decide_approval,
    get_approval_request,
    list_approval_requests,
)
from ticket_actions import execute_approved_action

logger = logging.getLogger(__name__)

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


class KnowledgeQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")


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
        logger.exception("Ticket analysis failed.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ticket analysis is temporarily unavailable.",
        )

    return result


@app.post(
    "/ask-knowledge",
    responses={
        503: {
            "description": "The local RAG service is temporarily unavailable."
        }
    },
)
def ask_knowledge(request: KnowledgeQuestionRequest):
    try:
        result = answer_question(request.question)
    except Exception:
        logger.exception("Knowledge question failed.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge service is temporarily unavailable.",
        )

    return result


# Ticket endpoints: all require a valid API key.

@app.post(
    "/tickets",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
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


@app.get(
    "/tickets",
    dependencies=[Depends(require_api_key)],
)
def get_tickets():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM tickets ORDER BY id"
        ).fetchall()

        return [dict(row) for row in rows]


@app.get(
    "/tickets/{ticket_id}",
    dependencies=[Depends(require_api_key)],
)
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


@app.patch(
    "/tickets/{ticket_id}",
    dependencies=[Depends(require_api_key)],
)
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


# Approval endpoints: all require a valid API key.

@app.get(
    "/approvals",
    dependencies=[Depends(require_api_key)],
)
def get_approvals(
    approval_status: str | None = Query(
        default=None,
        alias="status",
        pattern="^(pending|approved|rejected)$",
    ),
):
    """List approval requests, optionally filtered by status."""
    return list_approval_requests(status=approval_status)


@app.get(
    "/approvals/{request_id}",
    dependencies=[Depends(require_api_key)],
)
def get_approval(request_id: str):
    """Retrieve one approval request."""
    request = get_approval_request(request_id)

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found.",
        )

    return request


@app.post(
    "/approvals/{request_id}/decision",
    dependencies=[Depends(require_reviewer)],
)
def review_approval(
    request_id: str,
    decision_request: ApprovalDecisionRequest,
    reviewer: str = Depends(require_reviewer),
):
    """Approve or reject a pending request."""
    try:
        return decide_approval(
            request_id=request_id,
            decision=decision_request.decision,
            decided_by=reviewer,
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Approval request not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )


@app.post(
    "/approvals/{request_id}/execute",
    dependencies=[Depends(require_api_key)],
)
def execute_approval(request_id: str):
    """Execute an approved action exactly once."""
    try:
        return execute_approved_action(request_id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Approval request not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )
