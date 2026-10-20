
from uuid import uuid4

from database import DATABASE_NAME, get_connection


SUPPORTED_ACTIONS = {"close_ticket", "reopen_ticket"}
APPROVAL_STATUSES = {"pending", "approved", "rejected"}


def create_approval_request(
    action: str,
    ticket_id: int,
    requested_by: str,
    database_name: str = DATABASE_NAME,
) -> dict:
    """Persist a new approval request without executing its action."""

    if action not in SUPPORTED_ACTIONS:
        raise ValueError("Unsupported action.")

    if type(ticket_id) is not int or ticket_id < 1:
        raise ValueError("ticket_id must be a positive integer.")

    if not isinstance(requested_by, str) or not requested_by.strip():
        raise ValueError("requested_by must not be empty.")

    request_id = str(uuid4())

    with get_connection(database_name) as connection:
        ticket = connection.execute(
            "SELECT id FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        if ticket is None:
            raise ValueError("Ticket not found.")

        connection.execute(
            """
            INSERT INTO approval_requests (
                request_id,
                action,
                ticket_id,
                requested_by,
                status
            )
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (
                request_id,
                action,
                ticket_id,
                requested_by.strip(),
            ),
        )

        row = connection.execute(
            """
            SELECT *
            FROM approval_requests
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()

    return dict(row)


def get_approval_request(
    request_id: str,
    database_name: str = DATABASE_NAME,
) -> dict | None:
    """Retrieve one persisted approval request."""

    with get_connection(database_name) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM approval_requests
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()

    return dict(row) if row is not None else None


def list_approval_requests(
    status: str | None = None,
    database_name: str = DATABASE_NAME,
) -> list[dict]:
    """List approval requests, optionally filtered by status."""

    if status is not None and status not in APPROVAL_STATUSES:
        raise ValueError("Invalid approval status.")

    with get_connection(database_name) as connection:
        if status is None:
            rows = connection.execute(
                """
                SELECT *
                FROM approval_requests
                ORDER BY created_at DESC, request_id
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT *
                FROM approval_requests
                WHERE status = ?
                ORDER BY created_at DESC, request_id
                """,
                (status,),
            ).fetchall()

    return [dict(row) for row in rows]

def decide_approval(
    request_id: str,
    decision: str,
    decided_by: str,
    database_name: str = DATABASE_NAME,
) -> dict:
    """Record a human decision on a pending approval request."""

    if decision not in {"approved", "rejected"}:
        raise ValueError("Decision must be approved or rejected.")

    if not isinstance(decided_by, str) or not decided_by.strip():
        raise ValueError("decided_by must not be empty.")

    with get_connection(database_name) as connection:
        cursor = connection.execute(
            """
            UPDATE approval_requests
            SET status = ?,
                decided_at = CURRENT_TIMESTAMP,
                decided_by = ?
            WHERE request_id = ?
              AND status = 'pending'
            """,
            (decision, decided_by.strip(), request_id),
        )

        if cursor.rowcount == 0:
            existing = connection.execute(
                """
                SELECT request_id, status
                FROM approval_requests
                WHERE request_id = ?
                """,
                (request_id,),
            ).fetchone()

            if existing is None:
                raise ValueError("Approval request not found.")

            raise ValueError(
                "Only pending approval requests can be decided."
            )

        row = connection.execute(
            """
            SELECT *
            FROM approval_requests
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()

    return dict(row)
