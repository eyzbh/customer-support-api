
import sqlite3

import pytest

from approval_service import create_approval_request, decide_approval
from ticket_actions import close_ticket


def create_test_database(database_name):
    """Create an isolated database with one test ticket."""

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
            "INSERT INTO tickets (id, status) VALUES (12, 'open')"
        )


def read_ticket_status(database_name, ticket_id):
    with sqlite3.connect(database_name) as connection:
        row = connection.execute(
            "SELECT status FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

    return row[0] if row else None


def test_approved_request_closes_ticket(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)

    request = create_approval_request(
        "close_ticket", 12, "support-agent"
    )
    decide_approval(request, "approved")

    result = close_ticket(request, database_name)

    assert result == {"id": 12, "status": "closed"}
    assert read_ticket_status(database_name, 12) == "closed"


def test_pending_request_cannot_close_ticket(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)

    request = create_approval_request(
        "close_ticket", 12, "support-agent"
    )

    with pytest.raises(PermissionError, match="requires approval"):
        close_ticket(request, database_name)

    assert read_ticket_status(database_name, 12) == "open"


def test_rejected_request_cannot_close_ticket(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)

    request = create_approval_request(
        "close_ticket", 12, "support-agent"
    )
    decide_approval(request, "rejected")

    with pytest.raises(PermissionError, match="requires approval"):
        close_ticket(request, database_name)

    assert read_ticket_status(database_name, 12) == "open"


def test_wrong_action_cannot_close_ticket(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)

    request = create_approval_request(
        "reopen_ticket", 12, "support-agent"
    )
    decide_approval(request, "approved")

    with pytest.raises(ValueError, match="not for closing"):
        close_ticket(request, database_name)

    assert read_ticket_status(database_name, 12) == "open"


def test_missing_ticket_raises_error(tmp_path):
    database_name = str(tmp_path / "test.db")
    create_test_database(database_name)

    request = create_approval_request(
        "close_ticket", 99, "support-agent"
    )
    decide_approval(request, "approved")

    with pytest.raises(ValueError, match="Ticket not found"):
        close_ticket(request, database_name)
