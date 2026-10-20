
from dataclasses import dataclass
from typing import Literal
from uuid import uuid4


ApprovalStatus = Literal["pending", "approved", "rejected"]


@dataclass
class ApprovalRequest:
    """Represent a proposed action that requires human approval."""

    request_id: str
    action: str
    ticket_id: int
    requested_by: str
    status: ApprovalStatus = "pending"


def create_approval_request(
    action: str,
    ticket_id: int,
    requested_by: str,
) -> ApprovalRequest:
    """Create a pending approval request without executing the action."""

    if action not in {"close_ticket", "reopen_ticket"}:
        raise ValueError("Unsupported action.")

    if type(ticket_id) is not int or ticket_id < 1:
        raise ValueError("ticket_id must be a positive integer.")

    if not requested_by.strip():
        raise ValueError("requested_by must not be empty.")

    return ApprovalRequest(
        request_id=str(uuid4()),
        action=action,
        ticket_id=ticket_id,
        requested_by=requested_by.strip(),
    )


def decide_approval(
    request: ApprovalRequest,
    decision: str,
) -> ApprovalRequest:
    """Record an approval or rejection for a pending request."""

    if request.status != "pending":
        raise ValueError("Only pending requests can be decided.")

    if decision not in {"approved", "rejected"}:
        raise ValueError("Decision must be approved or rejected.")

    request.status = decision
    return request

def require_approval(request: ApprovalRequest) -> None:
    """Prevent execution unless a request has been approved."""

    if request.status != "approved":
        raise PermissionError(
            "The action requires approval before execution."
        )
