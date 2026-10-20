
from database import DATABASE_NAME, get_connection


def execute_approved_action(
    request_id: str,
    database_name: str = DATABASE_NAME,
) -> dict:
    """Execute an approved action once, recording execution atomically."""

    with get_connection(database_name) as connection:
        request = connection.execute(
            """
            SELECT request_id, action, ticket_id, status, executed_at
            FROM approval_requests
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()

        if request is None:
            raise ValueError("Approval request not found.")

        if request["status"] != "approved":
            raise PermissionError(
                "The action requires approval before execution."
            )

        if request["executed_at"] is not None:
            raise ValueError("This approval request was already executed.")

        action_statuses = {
            "close_ticket": "closed",
            "reopen_ticket": "open",
        }

        action = request["action"]

        if action not in action_statuses:
            raise ValueError("Unsupported action.")

        ticket = connection.execute(
            "SELECT id, status FROM tickets WHERE id = ?",
            (request["ticket_id"],),
        ).fetchone()

        if ticket is None:
            raise ValueError("Ticket not found.")

        # Claim the request within the same transaction as the ticket update.
        cursor = connection.execute(
            """
            UPDATE approval_requests
            SET executed_at = CURRENT_TIMESTAMP
            WHERE request_id = ?
              AND status = 'approved'
              AND executed_at IS NULL
            """,
            (request_id,),
        )

        if cursor.rowcount != 1:
            raise ValueError(
                "This approval request was already executed or is not approved."
            )

        connection.execute(
            """
            UPDATE tickets
            SET status = ?
            WHERE id = ?
            """,
            (action_statuses[action], request["ticket_id"]),
        )

        updated_ticket = connection.execute(
            """
            SELECT id, status
            FROM tickets
            WHERE id = ?
            """,
            (request["ticket_id"],),
        ).fetchone()

        return dict(updated_ticket)


def close_ticket(
    request_id: str,
    database_name: str = DATABASE_NAME,
) -> dict:
    """Close a ticket using an approved close-ticket request."""

    with get_connection(database_name) as connection:
        request = connection.execute(
            """
            SELECT action
            FROM approval_requests
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()

    if request is None:
        raise ValueError("Approval request not found.")

    if request["action"] != "close_ticket":
        raise ValueError("Approval request is not for closing a ticket.")

    return execute_approved_action(request_id, database_name)
