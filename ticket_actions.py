
from approval_service import ApprovalRequest, require_approval
from database import get_connection


def close_ticket(
    request: ApprovalRequest,
    database_name: str = "support.db",
) -> dict:
    """Close a ticket only after its action has been approved."""

    require_approval(request)

    if request.action != "close_ticket":
        raise ValueError("Approval request is not for closing a ticket.")

    with get_connection(database_name) as connection:
        cursor = connection.execute(
            """
            UPDATE tickets
            SET status = 'closed'
            WHERE id = ?
            """,
            (request.ticket_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError("Ticket not found.")

        row = connection.execute(
            """
            SELECT id, status
            FROM tickets
            WHERE id = ?
            """,
            (request.ticket_id,),
        ).fetchone()

    return dict(row)
