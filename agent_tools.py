
from database import get_connection


def get_ticket(ticket_id: int) -> dict | None:
    """Retrieve a support ticket by its ID."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                customer_name,
                email,
                subject,
                description,
                priority,
                status
            FROM tickets
            WHERE id = ?
            """,
            (ticket_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)
