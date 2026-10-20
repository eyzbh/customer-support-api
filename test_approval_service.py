
import pytest

from approval_service import create_approval_request, decide_approval, require_approval


def test_create_approval_request_starts_pending():
    request = create_approval_request(
        action="close_ticket",
        ticket_id=12,
        requested_by="support-agent",
    )

    assert request.action == "close_ticket"
    assert request.ticket_id == 12
    assert request.requested_by == "support-agent"
    assert request.status == "pending"
    assert request.request_id


def test_each_request_has_a_unique_id():
    first = create_approval_request("close_ticket", 12, "agent")
    second = create_approval_request("close_ticket", 12, "agent")

    assert first.request_id != second.request_id


def test_rejects_unsupported_action():
    with pytest.raises(ValueError, match="Unsupported action"):
        create_approval_request("delete_ticket", 12, "agent")


@pytest.mark.parametrize("ticket_id", [0, -1, True, "12", 1.5])
def test_rejects_invalid_ticket_id(ticket_id):
    with pytest.raises(ValueError, match="positive integer"):
        create_approval_request("close_ticket", ticket_id, "agent")


def test_rejects_empty_requester():
    with pytest.raises(ValueError, match="must not be empty"):
        create_approval_request("close_ticket", 12, "   ")

def test_approval_can_be_approved():
    request = create_approval_request("close_ticket", 12, "agent")

    result = decide_approval(request, "approved")

    assert result.status == "approved"


def test_approval_can_be_rejected():
    request = create_approval_request("close_ticket", 12, "agent")

    result = decide_approval(request, "rejected")

    assert result.status == "rejected"


def test_invalid_decision_is_rejected():
    request = create_approval_request("close_ticket", 12, "agent")

    with pytest.raises(ValueError, match="Decision must be"):
        decide_approval(request, "maybe")


def test_decided_request_cannot_be_decided_again():
    request = create_approval_request("close_ticket", 12, "agent")
    decide_approval(request, "approved")

    with pytest.raises(ValueError, match="Only pending requests"):
        decide_approval(request, "rejected")

def test_pending_request_cannot_execute():
    request = create_approval_request("close_ticket", 12, "agent")

    with pytest.raises(PermissionError, match="requires approval"):
        require_approval(request)


def test_rejected_request_cannot_execute():
    request = create_approval_request("close_ticket", 12, "agent")
    decide_approval(request, "rejected")

    with pytest.raises(PermissionError, match="requires approval"):
        require_approval(request)


def test_approved_request_passes_execution_guard():
    request = create_approval_request("close_ticket", 12, "agent")
    decide_approval(request, "approved")

    assert require_approval(request) is None
