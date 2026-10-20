
import sqlite3

import pytest

from persistent_approval_service import (
    create_approval_request,
    get_approval_request,
     decide_approval,
    list_approval_requests,
)


@pytest.fixture
def approval_database(tmp_path):
    database_path = str(tmp_path / "test_support.db")

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'open'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE approval_requests (
                request_id TEXT PRIMARY KEY,
                action TEXT NOT NULL
                    CHECK (action IN ('close_ticket', 'reopen_ticket')),
                ticket_id INTEGER NOT NULL,
                requested_by TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                decided_at TEXT,
                decided_by TEXT,
                executed_at TEXT,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO tickets (
                customer_name, email, subject, description
            )
            VALUES (?, ?, ?, ?)
            """,
            ("Test Customer", "test@example.com", "Test ticket", "Test description"),
        )

    return database_path


def test_create_persists_pending_request(approval_database):
    request = create_approval_request(
        "close_ticket", 1, "test-agent", approval_database
    )

    saved_request = get_approval_request(
        request["request_id"], approval_database
    )

    assert saved_request is not None
    assert saved_request["action"] == "close_ticket"
    assert saved_request["ticket_id"] == 1
    assert saved_request["requested_by"] == "test-agent"
    assert saved_request["status"] == "pending"
    assert saved_request["decided_at"] is None
    assert saved_request["executed_at"] is None


def test_list_requests_can_filter_by_status(approval_database):
    create_approval_request(
        "close_ticket", 1, "test-agent", approval_database
    )

    assert len(list_approval_requests(database_name=approval_database)) == 1
    assert len(
        list_approval_requests("pending", approval_database)
    ) == 1
    assert list_approval_requests("approved", approval_database) == []


def test_request_survives_database_reconnection(approval_database):
    request = create_approval_request(
        "reopen_ticket", 1, "test-agent", approval_database
    )

    # get_approval_request opens a new database connection.
    saved_request = get_approval_request(
        request["request_id"], approval_database
    )

    assert saved_request["status"] == "pending"
    assert saved_request["action"] == "reopen_ticket"


@pytest.mark.parametrize(
    ("action", "ticket_id", "requested_by"),
    [
        ("delete_ticket", 1, "test-agent"),
        ("close_ticket", 0, "test-agent"),
        ("close_ticket", -1, "test-agent"),
        ("close_ticket", 1, ""),
    ],
)
def test_invalid_request_is_rejected(
    approval_database, action, ticket_id, requested_by
):
    with pytest.raises(ValueError):
        create_approval_request(
            action, ticket_id, requested_by, approval_database
        )


def test_request_for_missing_ticket_is_rejected(approval_database):
    with pytest.raises(ValueError, match="Ticket not found"):
        create_approval_request(
            "close_ticket", 999, "test-agent", approval_database
        )


def test_invalid_status_filter_is_rejected(approval_database):
    with pytest.raises(ValueError, match="Invalid approval status"):
        list_approval_requests("unknown", approval_database)

def test_human_can_approve_pending_request(approval_database):
    request = create_approval_request(
        "close_ticket", 1, "test-agent", approval_database
    )

    decided = decide_approval(
        request["request_id"],
        "approved",
        "human-reviewer",
        approval_database,
    )

    assert decided["status"] == "approved"
    assert decided["decided_by"] == "human-reviewer"
    assert decided["decided_at"] is not None
    assert decided["executed_at"] is None


def test_human_can_reject_pending_request(approval_database):
    request = create_approval_request(
        "close_ticket", 1, "test-agent", approval_database
    )

    decided = decide_approval(
        request["request_id"],
        "rejected",
        "human-reviewer",
        approval_database,
    )

    assert decided["status"] == "rejected"
    assert decided["decided_by"] == "human-reviewer"


def test_cannot_decide_request_twice(approval_database):
    request = create_approval_request(
        "close_ticket", 1, "test-agent", approval_database
    )

    decide_approval(
        request["request_id"],
        "approved",
        "human-reviewer",
        approval_database,
    )

    with pytest.raises(ValueError, match="Only pending"):
        decide_approval(
            request["request_id"],
            "rejected",
            "another-reviewer",
            approval_database,
        )


def test_decision_for_missing_request_is_rejected(approval_database):
    with pytest.raises(ValueError, match="not found"):
        decide_approval(
            "nonexistent-request",
            "approved",
            "human-reviewer",
            approval_database,
        )


def test_invalid_decision_is_rejected(approval_database):
    request = create_approval_request(
        "close_ticket", 1, "test-agent", approval_database
    )

    with pytest.raises(ValueError, match="Decision must"):
        decide_approval(
            request["request_id"],
            "maybe",
            "human-reviewer",
            approval_database,
        )
