
import sqlite3

import pytest

from persistent_approval_service import (
    create_approval_request,
    decide_approval,
)
from ticket_actions import close_ticket, execute_approved_action


def create_test_database(database_name):
    """Create an isolated database with a ticket and approval table."""

    with sqlite3.connect(database_name) as connection:
        connection.execute(
            """
            CREATE TABLE tickets (
                id INTEGER PRIMARY KEY,
                status TEXT NOT NULL
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
            "INSERT INTO tickets (id, status) VALUES (12, 'open')"
        )


def read_ticket_status(database_name, ticket_id):
    with sqlite3.connect(database_name) as connection:
        row = connection.execute(
            "SELECT status FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

    return row[0] if row else None


def make_request(database_name, action="close_ticket", ticket_id=12):
    return create_approval_request(
        action,
        ticket_id,
        "support-agent",
        database_name,
    )


def test_approved_request_closes_ticket(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)
    request = make_request(database_name)

    decide_approval(
        request["request_id"], "approved", "human-reviewer", database_name
    )

    result = close_ticket(request["request_id"], database_name)

    assert result == {"id": 12, "status": "closed"}
    assert read_ticket_status(database_name, 12) == "closed"


def test_pending_request_cannot_close_ticket(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)
    request = make_request(database_name)

    with pytest.raises(PermissionError, match="requires approval"):
        close_ticket(request["request_id"], database_name)

    assert read_ticket_status(database_name, 12) == "open"


def test_rejected_request_cannot_close_ticket(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)
    request = make_request(database_name)

    decide_approval(
        request["request_id"], "rejected", "human-reviewer", database_name
    )

    with pytest.raises(PermissionError, match="requires approval"):
        close_ticket(request["request_id"], database_name)

    assert read_ticket_status(database_name, 12) == "open"


def test_wrong_action_cannot_close_ticket(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)
    request = make_request(database_name, "reopen_ticket")

    decide_approval(
        request["request_id"], "approved", "human-reviewer", database_name
    )

    with pytest.raises(ValueError, match="not for closing"):
        close_ticket(request["request_id"], database_name)

    assert read_ticket_status(database_name, 12) == "open"



def test_missing_ticket_raises_error(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)

    request = make_request(database_name, ticket_id=12)

    decide_approval(
        request["request_id"],
        "approved",
        "human-reviewer",
        database_name,
    )

    with sqlite3.connect(database_name) as connection:
        connection.execute(
            "DELETE FROM tickets WHERE id = ?",
            (12,),
        )

    with pytest.raises(ValueError, match="Ticket not found"):
        close_ticket(request["request_id"], database_name)


def test_request_cannot_execute_twice(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)
    request = make_request(database_name)

    decide_approval(
        request["request_id"], "approved", "human-reviewer", database_name
    )

    close_ticket(request["request_id"], database_name)

    with pytest.raises(ValueError, match="already executed"):
        close_ticket(request["request_id"], database_name)


def test_approved_request_can_reopen_ticket(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)

    with sqlite3.connect(database_name) as connection:
        connection.execute(
            "UPDATE tickets SET status = 'closed' WHERE id = 12"
        )

    request = make_request(database_name, "reopen_ticket")

    decide_approval(
        request["request_id"], "approved", "human-reviewer", database_name
    )

    result = execute_approved_action(
        request["request_id"], database_name
    )

    assert result == {"id": 12, "status": "open"}
